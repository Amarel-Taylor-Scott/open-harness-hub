# THE DESIGN BIBLE — AI Done Right · the single, designer-ready design-system reference

> The visual/UX counterpart to `docs/BIBLE.md` (the *what + why + laws*). This is the **how it looks + how it's
> built**, detailed enough to hand to a designer (human or Claude-acting-as-designer) so they can understand,
> reproduce, and extend the system. Every value here is **quoted from the source code** — never re-hardcode a hex
> (No-Magic-Values applies to design too); the file the value lives in is named in-line. This doc is one of the **5
> CANONICAL docs** tracked by `scripts/check_context_freshness.py`
> (`CLAUDE.md · AGENTS.md · docs/NORTHSTAR.md · docs/BIBLE.md · docs/DESIGN-BIBLE.md`) — keep its file references real.
> Last reconciled **2026-06-26**. `serves_truth = false` (the surfaces render candidate output; only Baltor's governed
> source answers serve truth).

**Single sources this doc is generated from (read these, don't trust the prose over the code):**

| Source file | What it is |
|---|---|
| `scripts/surface_server.py` | THE canonical renderer. Its `_CSS_TEMPLATE` constant is the live stylesheet every surface ships **byte-identical** (7959 chars rendered). One handler, all routes, all 5 surfaces. |
| `scripts/check_surface_server.py` | The enforcement — **122 assertions** (computed, run it): byte-identical CSS, nav links all 5, governed `/demo` + `/run`, faceted `/browse`, hub index, `serves_truth=false`. |
| `architecture/surface_capability_spec.json` | `pillars[]` = the 5 surfaces (id · accent · brand · role · capabilities). The config the renderer reads. |
| `scripts/_surface_accents.py` | `accent(id)` — the per-surface hex, read from the spec (no hard-coded hex in the server). |
| `src/teleon/demos/byo_key_demo.py` | `DEMOS` (label · needs_key · runner) + `run_byo_demo` — the governed BYO-key plane. |
| `scripts/byo_demo_server.py` | `EXAMPLE` — the per-surface demo example prompts (reused, not re-invented). |
| `src/teleon/registry/browse.py` | `FACET_DIMS` + `browse()` — the faceted catalog the `/browse` route renders. |
| `dist/surface-urls.json` | The public/tunnel URL per surface (cross-surface nav reads it; robust if absent). |
| `dist/sites/openharness-design/shared/oh-tokens.css` | The high-fidelity bundle the canonical mirrors (dir-a · theme-light palette). |

---

## 1. The one design law

**ONE design system. Every surface ships BYTE-IDENTICAL CSS. The accent color and the copy are the ONLY per-surface
variables.**

The standardization point is `surface_css(accent)` in `scripts/surface_server.py`: it takes the single
`_CSS_TEMPLATE` constant and replaces the one `__ACCENT__` token with the surface's hex. The token appears **exactly
once**, so the rendered stylesheet is identical across all five surfaces except that one value.

- Rendered stylesheet length: **7959 chars**, identical on every surface (`_CSS_TEMPLATE` is 7962 chars including the
  10-char `__ACCENT__` placeholder; a 7-char hex → 7962 − 10 + 7 = **7959**).
- `scripts/check_surface_server.py` proves it (run `python3 scripts/check_surface_server.py --self-test` → **122
  assertions PASS**). The load-bearing assertions:
  - `len({css.replace(accent,"__ACCENT__") for each surface}) == 1` — strip the accent and all 5 stylesheets collapse to one string;
  - that one string `== _CSS_TEMPLATE` (the canonical template, no drift);
  - `css.count(accent) == 1` per surface (the accent is the *only* difference);
  - all 5 accents distinct; `font-family:"Inter"` present; the canonical token block present.

**Consequence for a designer:** you never style a surface. You edit `_CSS_TEMPLATE` once and the change propagates to
all 5. There are no per-surface stylesheets, overrides, or forks — by law.

---

## 2. The canonical decision + reconciliation

**Owner-decided 2026-06-26: one design system — LIGHT theme, Inter UI font (+ `ui-monospace` for code/labels/eyebrows),
rendered by one config-driven server.** This **supersedes** the prior "Hanken Grotesk / `oh-site.jsx`" canonical.

Reconciliation (explicit, so the contradiction is closed, not orphaned):

- **Superseded:** the earlier DESIGN-BIBLE described a multi-theme React bundle (`oh-site.jsx` + `products.js`, light +
  dark, 8 design directions A–H + S) and named **Hanken Grotesk** as the UI font. "Hanken Grotesk" was only ever a
  *display* font in two bundle directions (`dir-d`, `dir-s`); the bundle's UI sans has always been **Inter**
  (`--font-sans: "Inter", …` in `oh-tokens.css`). The live renderer resolves that to a single answer: **Inter UI**.
- **Canonical now:** `scripts/surface_server.py` renders all 5 surfaces from one `_CSS_TEMPLATE`. Its tokens mirror the
  high-fidelity bundle's **`dir-a` · `theme-light`** palette (warm paper) from
  `dist/sites/openharness-design/shared/oh-tokens.css`. The bundle remains the canonical *source of record* for the
  richer component library; the server is the canonical *renderer* for the 5 shipped surfaces.
- **Warrant:** clear owner intent (2026-06-26) for one standardized server; corroborated by the bundle's own
  `--font-sans: Inter` and `dir-a.theme-light` neutrals. Design/brand changes require owner intent — this carries it.

---

## 3. The 5 surfaces

Read from `architecture/surface_capability_spec.json` (`pillars[]`); accent via `scripts/_surface_accents.py`.

| id | brand (rendered) | accent | role | routes served |
|---|---|---|---|---|
| `ai-done-right` | **AI Done Right** | `#5a6b87` | parent / holding brand — the **portfolio HUB / index** | `/` (hub index) · `/demo` (pick-a-surface) |
| `teleon` | **Teleon.dev** | `#6d5ef0` | purpose-driven, eval-gated, self-adaptive compute runtime | `/` · `/demo` (BYO key) · `POST /run` |
| `baltor` | **Baltor.ai** | `#0e7c86` | managed, verified, provable context, powered by Teleon — governs TRUTH | `/` · `/demo` (BYO key) · `POST /run` |
| `aidevobserver` | **AIDevObserver** | `#b25fd6` | watches AI USAGE — reviews the SESSION (post) + helps intra-session | `/` · `/demo` (**no key**) · `POST /run` |
| `open-star-hubs` | **Open\*Hubs** | `#3b6fd4` | the open STORE both products consume + the open CapabilityTask spec (CTS) | `/` · `/demo` (BYO key) · **`/browse`** · `POST /run` |

Notes: `ai-done-right` is the parent — its home is the **portfolio index** (a card per other surface) and it has no
BYO demo panel of its own (its `/demo` is a "pick a surface" index). Only `open-star-hubs` serves `/browse` (the
faceted registry catalog); the other four 404 on `/browse`. Domain mapping in §10.

---

## 4. Color system — the full token palette

The complete `:root` palette from `_CSS_TEMPLATE` (in `scripts/surface_server.py`). These mirror `oh-tokens.css`
`.oh.dir-a.theme-light` (warm editorial "paper"). Every visual value is a `var(--token)` reference — there are **no
raw hexes outside `:root`** except the injected accent.

| Token | Value | Meaning | Where used |
|---|---|---|---|
| `--bg` | `#faf7f0` | warm paper page background | `body` background; the nav's translucent layer `rgba(250,247,240,.82)` is this color |
| `--bg-subtle` | `#f3eee2` | one step down from `--bg` | nav-link hover, output panel `.out`, chips `.chip`, focus-ring glow |
| `--surface` | `#fffdf8` | raised card/panel paper (near-white) | `.card`, `.panel`, `.rec`, `.pill`, `.eyebrow`, active nav-link |
| `--fg` | `#1c1b19` | primary ink (near-black, warm) | `body` text, headings, `.nav-brand`, `.rid` |
| `--fg-muted` | `#6b675e` | secondary text | ledes, card body, `.role`, labels, nav-link rest, `.holds` |
| `--fg-faint` | `#868074` | tertiary / metadata text | `.note`, `.footer`, `.facet h3`, `.fmore`, `.fv .ct`, badge text default |
| `--border` | `#e7e0d2` | hairline divider / outline | all `1px solid var(--border)` borders, nav bottom, footer top |
| `--accent` | **per-surface** (`__ACCENT__`) | the one brand variable | links, `.btn-accent`, `.nav-dot`, active states, hover borders, eyebrow text, `.idx`, `.arrow` |
| `--accent-ink` | `#ffffff` | text/ink ON the accent fill | `.btn-accent` label text |

The **five accents** (single source: `architecture/surface_capability_spec.json` → `scripts/_surface_accents.py`):

| Surface | `--accent` | hue |
|---|---|---|
| AI Done Right | `#5a6b87` | slate blue |
| Teleon.dev | `#6d5ef0` | indigo |
| Baltor.ai | `#0e7c86` | teal (the "verified/moat" color) |
| AIDevObserver | `#b25fd6` | orchid / violet |
| Open\*Hubs | `#3b6fd4` | royal blue |

Color rule for a designer: spend the accent on *intent* (primary action, the active item, the brand dot, a focused
field). Everything structural is a neutral token. Contrast: all accents are AA on `--surface`/`--bg`; `--accent-ink`
(white) is the only thing placed on an accent fill.

---

## 5. Typography

**Inter** is the UI font; **`ui-monospace`** is the code/label/eyebrow font. No serif, no display face in the live
renderer.

- **Loading** (`_GOOGLE_FONTS` in `surface_server.py`, in every page `<head>`):
  ```html
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
  ```
  Five weights are loaded: **400, 500, 600, 700, 800**.
- **Body stack:** `font-family:"Inter",-apple-system,"Segoe UI",system-ui,sans-serif` with `line-height:1.6`,
  `-webkit-font-smoothing:antialiased`, `text-rendering:optimizeLegibility`.
- **Mono stack:** `.mono` / `.mono-in` / eyebrows / counts use
  `font-family:ui-monospace,SFMono-Regular,monospace` (system mono — nothing to download).

**The type scale** (every size is pulled verbatim from `_CSS_TEMPLATE`):

| Role | Selector | Size | Weight / tracking |
|---|---|---|---|
| Hero H1 | `.hero h1` | `clamp(2.3rem,5.2vw,3.7rem)` | 800 · `letter-spacing:-.028em` · `line-height:1.04` |
| Lede | `.hero .lede` | `clamp(1.05rem,2vw,1.3rem)` | `--fg-muted` · `max-width:46ch` |
| Section H2 | `.section-head h2` | `1.55rem` | 700 · `-.02em` |
| Card H3 | `.card h3` | `1.1rem` | `-.01em` · `line-height:1.25` |
| Nav brand | `.nav-brand` | `1.02rem` | 800 · `-.01em` |
| Body | `body` | `1rem` (browser default) | 400 · `line-height:1.6` |
| Button | `.btn` | `.96rem` | 600 |
| Card body | `.card p` / `.card .role` | `.93rem` | `--fg-muted` |
| Nav link · card arrow | `.nav-link` / `.card .arrow` | `.88rem` | 500 / 600 |
| Record id · facet value | `.rid` / `.fv` | `.86rem` | `.rid` mono 700 |
| Footer | `.footer` | `.85rem` | `--fg-faint` |
| Label | `label` | `.82rem` | 600 · `--fg-muted` |
| Pill | `.pill` | `.78rem` | `--fg-muted` |
| Note (governance) | `.note` | `.77rem` | `--fg-faint` |
| Footer truth line | `.foot-truth` | `.76rem` | mono |
| Facet count | `.fv .ct` | `.74rem` | mono · `--fg-faint` |
| Eyebrow · card index | `.eyebrow` / `.card .idx` | `.72rem` | mono · UPPER `.16em` / lower `.03em` · `--accent` |
| Facet group head | `.facet h3` | `.71rem` | UPPER · `.09em` · `--fg-faint` |
| Badge | `.badge` | `.63rem` | UPPER · `.05em` |
| Inputs | `input,textarea` | `14px "Inter"` | — |
| Mono input | `.mono-in` | `13px` | mono |
| Output block | `.out` | `12.5px` | mono |

---

## 6. Spacing · radii · shadows · layout

All from `_CSS_TEMPLATE` `:root` + layout rules.

| Token | Value | Use |
|---|---|---|
| `--r-sm` | `8px` | buttons, nav-link, inputs, small chips/facet rows |
| `--r-md` | `12px` | cards, record cards, output block |
| `--r-lg` | `18px` | the demo `.panel` |
| `--maxw` | `1080px` | the page container width |
| `--shadow-sm` | `0 1px 2px rgba(60,40,20,.05)` | resting cards/panels/buttons (warm-brown shadow, not gray) |
| `--shadow-md` | `0 14px 38px rgba(60,40,20,.12)` | hover lift on cards + accent button |

- **Container:** `.wrap { max-width:var(--maxw); margin:0 auto; padding:0 1.4rem }` — every section centers in 1080px.
- **Card grid:** `.cards { display:grid; grid-template-columns:repeat(auto-fill,minmax(252px,1fr)); gap:1rem }` —
  responsive auto-fill; cards reflow with the viewport, no media query needed.
- **Record grid (browse):** `.reclist { … minmax(244px,1fr); gap:.85rem }`.
- **Pill radius** (`999px`) is inline on pills/chips/badges/eyebrow (fully round) — not tokenized.
- **Responsive** (`@media(max-width:760px)`): `.browse-layout` collapses to one column; `.facets` un-sticks
  (`position:static`); `.hero` padding tightens to `3.1rem 0 2rem`.

> Note: the bundle (`oh-tokens.css` dir-a) uses radii `6/9/12px` and `--e2: 0 10px 30px /.10`; the renderer retunes to
> `8/12/18px` and `--shadow-md: 0 14px 38px /.12`. The neutrals + `--shadow-sm` match exactly; the radii/`--surface`
> (`#fffdf8` vs panel `#ffffff`)/`--shadow-md` are intentional renderer tunings — see §11 (drift open-item).

---

## 7. Components

Documented from the real classes in `_CSS_TEMPLATE` and the render functions in `surface_server.py`. Each: structure,
classes, intent, snippet.

### 7.1 Sticky top nav — `nav(current_id)`
Brand (with accent dot) on the left; the 5 surface links on the right; the current surface link is `.active`.
Translucent, blurred, sticky. Classes: `.nav` (`position:sticky; top:0; z-index:50; background:rgba(250,247,240,.82);
backdrop-filter:saturate(180%) blur(12px)`), `.nav-inner`, `.nav-brand`, `.nav-dot` (`11px` accent square,
`border-radius:3px`), `.nav-links`, `.nav-link`, `.nav-link.active` (accent text on `--surface` with a `--border`).
```html
<nav class="nav"><div class="nav-inner">
  <a class="nav-brand" href="/"><span class="nav-dot"></span>Teleon.dev</a>
  <div class="nav-links">
    <a class="nav-link" href="https://…/">AI Done Right</a>
    <a class="nav-link active" href="/">Teleon.dev</a>
    <a class="nav-link" href="https://…/">Baltor.ai</a> … (all 5)
  </div>
</div></nav>
```
Intent: identical chrome on every surface; the accent dot + active link are the only brand tells.

### 7.2 Eyebrow — `.eyebrow`
A small uppercase mono kicker above the H1. Pill-shaped, `--surface` fill, `--border`, accent text. Intent: orient the
visitor (route/brand) without competing with the H1.
```html
<span class="eyebrow">/demo · bring your own key</span>
```

### 7.3 Hero — `_hero(eyebrow, h1, lede, cta, pills)`
Eyebrow → H1 → lede → CTA row (→ optional pills). Classes: `.hero`, `.hero h1`, `.hero .lede`, `.cta-row`.
```html
<header class="hero"><div class="wrap">
  <span class="eyebrow">AI Done Right</span>
  <h1>Teleon.dev</h1>
  <p class="lede">the purpose-driven, eval-gated, self-adaptive compute runtime</p>
  <div class="cta-row">
    <a class="btn btn-accent" href="/demo">Try the live demo →</a>
    <a class="btn btn-ghost" href="#capabilities">What it does ↓</a>
  </div>
</div></header>
```

### 7.4 Pills / chips — `.pills`/`.pill`, `.chips`/`.chip`
`.pill` = capability tags under the hub hero (`--surface` + `--border`, round). `.chip` = compact tags inside
record cards + active-filter removers (`--bg-subtle` fill). Intent: scannable metadata, never a primary action.
```html
<div class="pills"><span class="pill">Portfolio index → the pillars</span> …</div>
```

### 7.5 Buttons — `.btn`, `.btn-accent`, `.btn-ghost`
`.btn` = base (inline-flex, 600, `--r-sm`, lift on hover `translateY(-1px)`). `.btn-accent` = primary (accent fill,
`--accent-ink` text, `--shadow-sm` → `--shadow-md` on hover). `.btn-ghost` = secondary (`--surface` fill, `--border`).
One accent button per view, max.
```html
<a class="btn btn-accent" href="/browse">Browse the catalog →</a>
<a class="btn btn-ghost" href="#capabilities">What it does ↓</a>
```

### 7.6 Card grid — `_section` + `.cards`/`.card`
Auto-fill grid of cards. A card has a mono `.idx` kicker (accent), an `h3`, a body `p` / `.role`, and (when it's a
link) an `.arrow`. `a.card:hover` lifts (`translateY(-2px)`) and borders go accent. Two uses: portfolio surface
cards (`.card.surface-card`, hub home) and capability cards (`.idx` = `01`, `02`, …).
```html
<a class="card surface-card" href="https://…/">
  <div class="idx">teleon</div>
  <h3>Teleon.dev</h3>
  <p class="role">the purpose-driven, eval-gated, self-adaptive compute runtime</p>
  <span class="arrow">Visit Teleon.dev →</span>
</a>
```

### 7.7 BYO-key demo form — `render_demo` + `.panel`/`.field`/`.out`
A single `.panel` card: optional key field (password input, only when `needs_key`), a prompt `textarea` (pre-filled
from `EXAMPLE`), the governance `.note`, the accent run button, and a hidden `.out` block that reveals the JSON
result. Focus states ring the accent (`box-shadow:0 0 0 3px var(--bg-subtle)`). The `_RUN_JS` posts
`{demo,byo_key,inputs}` to `/run` and renders the JSON.
```html
<div class="panel">
  <div class="field"><label>Your API key (required)</label>
    <input class="mono-in" id="key" type="password" autocomplete="off" placeholder="sk-… or your provider key"></div>
  <div class="field"><label>Prompt</label>
    <textarea class="mono-in" id="prompt">summarize server logs into a cited incident report</textarea></div>
  <p class="note">Used only for this request · never stored · never logged. Only a redacted status (sk-…1234) is ever shown.</p>
  <button class="btn btn-accent" onclick="run()">Run with my key →</button>
  <div class="out" id="out"></div>
</div>
```
The AIDevObserver demo omits the key field (`needs_key:false`) and shows the no-key note instead.

### 7.8 Browse facet sidebar + record cards — `render_browse` (open-star-hubs only)
Two-column `.browse-layout` (`248px 1fr`): a sticky `.facets` aside on the left, a `.reclist` grid of `.rec` cards on
the right. A search `.search-row` and `.active-filters` chips sit above. Each `.facet` group lists `.fv` rows
(value + mono `.ct` count); the selected value is `.fv.on` (accent). Up to 15 values per group, then `.fmore`
("+N more"). Each `.rec` card: a mono `.rid`, a status `.badge`, a `.holds` line, and category `.chip`s.
```html
<div class="browse-layout">
  <aside class="facets">
    <div class="facet"><h3>Category</h3>
      <div class="fvals">
        <a class="fv" href="/browse?category=…"><span>tools</span><span class="ct">42</span></a>
        <a class="fv on" href="/browse"><span>context</span><span class="ct">7</span></a>
      </div>
      <div class="fmore">+12 more</div>
    </div> … (category · type · kind · layer · status)
  </aside>
  <section><div class="reclist">
    <div class="rec"><div class="rec-head">
      <span class="rid">component</span><span class="badge">active</span></div>
      <div class="holds">what this registry holds…</div>
      <div class="chips"><span class="chip">tools</span></div>
    </div> …
  </div></section>
</div>
```
Facet dimensions (single source `src/teleon/registry/browse.py` → `FACET_DIMS`):
**category · type · kind · layer · status**. Counts are computed by `browse()` — never typed.

### 7.9 Governance footer — `footer(current_id)`
A parent line, the 5 cross-surface links, and the mono **truth line**. Present on every page. Classes: `.footer`,
`.foot-links`, `.foot-truth.mono`.
```html
<footer class="footer"><div class="wrap">
  <div>AI Done Right — one standardized surface server · five product surfaces, one design system.</div>
  <div class="foot-links"><a href="…">AI Done Right</a> … (all 5)</div>
  <div class="foot-truth mono">serves_truth = false · candidate output, not verified truth ·
    a BYO key is used only for the request, never stored or logged.</div>
</div></footer>
```

---

## 8. Routes + layout per surface

One handler — `handle_get(surface_id, path, query)` — serves every surface (socket-free, so the proof drives it
directly):

| Route | Status | Renders | Notes |
|---|---|---|---|
| `GET /` | 200 | `render_home` | `ai-done-right` → portfolio index; others → hero + capability cards (+ a "browse" section for `open-star-hubs`) |
| `GET /demo` | 200 | `render_demo` | parent → "pick a surface" index; product surfaces → the BYO-key panel |
| `GET /browse` | 200 / 404 | `render_browse` | **`open-star-hubs` only**; every other surface → 404 |
| `GET /browse?<facet>=<v>` | 200 | filtered browse | facet filters parsed from the query string; counts recompute |
| `GET /favicon.ico` | **204** | empty | avoids a console 404 on every page |
| `POST /run` | 200 (JSON) | `_run_request` → `run_byo_demo` | the governed demo runner; any error is a JSON result, never a 500 |
| anything else | 404 | `render_404` | a styled 404 hero with a Home button |

**Per-surface home layout.** `ai-done-right` home = the **hub portfolio index**: hero ("The portfolio") + a
`surface-card` per other surface (id · brand · role · "Visit →"). The four product surfaces = hero (brand + role +
CTAs) → numbered capability cards (`Capabilities`). `open-star-hubs` additionally gets a "Browse every record" section
linking `/browse`. **Page assembly:** `page() = <!doctype> + <head>(title, Inter link, <style>surface_css(accent))
+ nav() + body + footer()`.

Responsive: the 1080px container is fluid; card/record grids auto-fill; the browse layout and hero collapse at
`max-width:760px` (§6). The nav wraps its links (`flex-wrap:wrap`) on narrow screens.

---

## 9. Governance in the UI

The design encodes the repo's truth/safety laws as visible UI — not just backend behavior:

- **`serves_truth = false`** on every page (the mono footer truth line; asserted on home + demo + browse by
  `check_surface_server.py`). The surfaces render *candidate* output; only Baltor's governed source answers serve
  truth.
- **BYO key is never stored or echoed.** `run_byo_demo` puts the key in a **transient** env scope
  (`OH_LLM_API_KEY`) for one call, then restores it; the result returns only a **redacted** status
  (`redact()` → `sk-…1234`). The proof injects `sk-secret-LEAK1234` and asserts the raw key never appears in the JSON.
  The UI mirrors this in the `.note`: *"Used only for this request · never stored · never logged."*
- **Honest-unavailable, no fake green.** A key-needing demo with no key returns `{"ok":false,"status":"needs_key"}`
  (not a fabricated answer). No reachable LLM lane → an honest "would call YOUR model…" note.
- **Candidate framing in browse.** Records carry a status `.badge`; the browse subhead states `serves_truth=false`;
  the unit is the record, hubs are facets (a record can sit under several categories).

---

## 10. Build + serve path

```bash
python3 scripts/surface_server.py <surface-id> [--port N]
# surface-id ∈ ai-done-right · teleon · baltor · aidevobserver · open-star-hubs
```

Default local ports (`DEFAULT_PORTS`): `ai-done-right 8001 · teleon 8002 · aidevobserver 8003 · baltor 8004 ·
open-star-hubs 8005`. Cross-surface nav reads `dist/surface-urls.json` (the launcher writes the public URLs there);
if a target URL is absent it falls back to `http://localhost:<default-port>/`. A link to the current surface is always
same-origin `/`.

| Surface | Production domain | Ephemeral (TryCloudflare quick tunnel) |
|---|---|---|
| AI Done Right | `aidoneright.dev` | written to `dist/surface-urls.json` per run (rotates) |
| Teleon.dev | `teleon.dev` | ″ |
| Baltor.ai | `baltor.ai` | ″ |
| AIDevObserver | `aidevobserver.io` | ″ |
| Open\*Hubs | `openhubforai.io` | ″ |

TryCloudflare URLs are **ephemeral** (they change every launch — `dist/surface-urls.json` is the live record);
production uses the stable domains above.

---

## 11. Handoff to a designer ("Claude design")

You can change the look of all 5 surfaces from a handful of single-source files. Edit once, it propagates.

### SAFE to change (single-source — propagates to all 5)
| To change… | Edit… | Effect |
|---|---|---|
| A surface's **accent** | `architecture/surface_capability_spec.json` → `pillars[].accent` (read by `_surface_accents.py`) | the one per-surface color; nothing else moves |
| A surface's **copy** (brand · role · capabilities) | `architecture/surface_capability_spec.json` | hero/cards/nav/footer text |
| **Demo copy** (label · example prompt · needs_key) | `src/teleon/demos/byo_key_demo.py` (`DEMOS`) + `scripts/byo_demo_server.py` (`EXAMPLE`) | the `/demo` panels |
| **Type scale, spacing, color tokens, component CSS** | `_CSS_TEMPLATE` in `scripts/surface_server.py` (ONE place) | every surface, identically |
| **Add a component** | add its CSS to `_CSS_TEMPLATE` **and** emit its HTML in the relevant `render_*`/helper | propagates to all 5 |

**How to extend a component (the pattern):** (1) add the rule(s) to `_CSS_TEMPLATE` using existing tokens
(`var(--surface)`, `var(--border)`, `var(--r-md)`, `var(--accent)`, `var(--shadow-sm)`) — do **not** introduce raw
hexes; (2) emit the markup in the matching render function (`_hero`, `_section`, `render_demo`, `render_browse`, …);
(3) re-run `python3 scripts/check_surface_server.py --self-test` — it re-derives the byte-identical-CSS invariant and
re-counts assertions; (4) if you add a new token, give it a unit/rationale and consider an assertion for it. Because
`_CSS_TEMPLATE` is one string shared by all surfaces, a new component is automatically consistent — that *is* the
single-source rule.

### LOCKED (do not break — owner law)
- The **byte-identical-CSS law**: accent + copy are the only per-surface variables. Never add a per-surface stylesheet,
  inline style that varies by surface, or a second `__ACCENT__`-like token. (`check_surface_server.py` will fail.)
- The **5-surface model** (the `pillars[]` set) and which surface owns `/browse` (`open-star-hubs`).
- The **governance footer** + `serves_truth=false` + the never-store/never-echo BYO-key contract.
- **Inter UI + `ui-monospace`** as the canonical fonts (changing the type *system* is a design decision requiring
  owner intent; resizing within the scale is safe).

### Open item (flag for a future drift-check)
`_CSS_TEMPLATE` **mirrors `oh-tokens.css` (`dir-a.theme-light`) by hand.** The neutrals
(`--bg #faf7f0`, `--bg-subtle #f3eee2`, `--fg #1c1b19`, `--fg-muted`, `--fg-faint`, `--border #e7e0d2`,
`--accent-ink #ffffff`, `--shadow-sm`) match exactly; the **radii** (`8/12/18` vs the bundle's `6/9/12`),
**`--surface`** (`#fffdf8` vs the bundle's `--panel #ffffff`), and **`--shadow-md`** (`0 14px 38px /.12` vs the
bundle's `--e2 0 10px 30px /.10`) are renderer-specific tunings. Nothing currently pins the two. **Recommended:** add a
drift-check (e.g. extend `check_surface_server.py`) that parses both files and asserts the shared tokens stay equal,
flagging intended divergences — so the mirror can't silently rot.

---

## 12. Evidence — the 5 live surfaces, verified

Two layers of evidence back this design system:

**Deterministic proof (always-on):** `python3 scripts/check_surface_server.py --self-test` →
**PASS, 122 assertions.** It proves, without a socket: all 5 homes are 200 HTML; the CSS is byte-identical except the
single accent and equals `_CSS_TEMPLATE`; Inter is loaded; the canonical token block is present; each nav links all 5;
`/demo` carries the governed "never stored" copy and shows a key field iff `needs_key`; `POST /run` is honest with no
key and redacts a real key (raw key never leaks); `/browse` renders facet groups with computed counts (and other
surfaces 404); the hub renders a portfolio card per surface; `serves_truth = false` everywhere; favicon is 204.

**Live render verification (Playwright):** each surface served (`surface_server.py <id> --port N`) and loaded in a real
browser — the expected values below are all code-grounded:

| Surface | computed `body` background | resolved UI font | `--accent` | console errors |
|---|---|---|---|---|
| AI Done Right | `#faf7f0` | Inter | `#5a6b87` | 0 |
| Teleon.dev | `#faf7f0` | Inter | `#6d5ef0` | 0 |
| Baltor.ai | `#faf7f0` | Inter | `#0e7c86` | 0 |
| AIDevObserver | `#faf7f0` | Inter | `#b25fd6` | 0 |
| Open\*Hubs | `#faf7f0` | Inter | `#3b6fd4` | 0 |

(Background `#faf7f0` = `--bg`; font = the loaded Inter face; accents = `_surface_accents`. The 0-console-errors result
is supported by the 204 favicon and the self-contained inline `<style>` — no missing assets beyond the Google-Fonts
link.) `serves_truth = false`.

---

## Appendix — file map (everything this doc references)

| Concern | File |
|---|---|
| Canonical renderer + `_CSS_TEMPLATE` | `scripts/surface_server.py` |
| Enforcement (122 assertions) | `scripts/check_surface_server.py` |
| 5 surfaces config (id · accent · brand · role · caps) | `architecture/surface_capability_spec.json` |
| Per-surface accent accessor | `scripts/_surface_accents.py` |
| BYO-key demo plane (`DEMOS`, `run_byo_demo`, redact) | `src/teleon/demos/byo_key_demo.py` |
| Demo example prompts (`EXAMPLE`) | `scripts/byo_demo_server.py` |
| Faceted browse (`FACET_DIMS`, `browse`) | `src/teleon/registry/browse.py` |
| Cross-surface URLs | `dist/surface-urls.json` |
| High-fidelity bundle tokens (mirrored) | `dist/sites/openharness-design/shared/oh-tokens.css` |
| Context-freshness (this is 1 of the 5 canonical docs) | `scripts/check_context_freshness.py` |
