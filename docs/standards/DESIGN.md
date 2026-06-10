# Baltor — DESIGN.md

A single, droppable design-system reference (schema from `VoltAgent/awesome-design-md`, ~87.5k★ —
verified 2026-06-04). Point any coding agent at this file so agent-generated screens match Baltor's
shipped aesthetic without a Figma pipeline.

**Grounding:** every value below is extracted from the **real shipped CSS** in `web/baltor/`
(primarily `dashboard.html`, the live-ops surface). This file DOCUMENTS the system as shipped — it
does not invent a new look. Where surfaces disagree, see **§Known drift** (an owner-decision item;
not resolved unilaterally here, since palette is brand territory).

---

## 1. Visual theme
Dark, compact, instrument-panel aesthetic — a governed "ops console", not a marketing gradient. The
product is a Context Engine you *watch run*: six macro stages + a verification rail, events firing
live. Tone: precise, dense, trustworthy, monospaced numbers. Acquired-AI-tool-grade; **not**
dev-dark-with-orange. A lighter "paper" variant exists for document/reading surfaces (§2).

## 2. Color palette & roles
**Dark ops surface (primary — `dashboard.html`):**
| Token | Value | Role |
|---|---|---|
| `--bg` | `#0a0d14` | app background |
| `--panel` | `#121723` | raised panel / card |
| `--panel2` | `#0e131d` | inset (stage card, stream row) |
| `--line` | `#1f2734` | hairline borders |
| `--ink` | `#e6edf6` | primary text |
| `--muted` | `#8aa0b6` | secondary/label text |
| `--emerald` | `#34d39a` | success · measured lift · "hot"/active stage |
| `--amber` | `#f5a623` | warning · reviews routed |
| `--blue` | `#5aa0ff` | info · accents |
| `--red` | `#ff6b6b` | contradiction · blocked · denied |
| `--purple` | `#a98bff` | anti-fragility / fragile-state accent |

**Stage-rail accents** (`--rail`, one hue per macro stage): amber · blue · bronze · green · violet —
used for the 7-card stage board / hero columns.

**Paper surface (reading/document variant):** `--paper #f7f9fc` · `--card #ffffff` ·
`--ink #0e1726` · `--line #e3e7ef` · `--accent #1d6fe0`. Use only for long-form/document views; the
product hero + dashboard stay on the dark ops surface.

## 3. Typography
- **Sans:** `Inter, system-ui, -apple-system, "Segoe UI", Roboto, sans-serif` (`--sans`) — UI text.
- **Mono:** `ui-monospace, SFMono-Regular, Menlo, Consolas, monospace` (`--mono`) — ALL numbers,
  metrics, event kinds, IDs, hashes, `ctx://` handles. Numbers are monospace by rule (it's an
  instrument panel).
- Labels: 11px uppercase, letter-spacing ~.4px, `--muted`. Metric values: ~20px mono.

## 4. Component stylings (with states)
- **Card / panel:** bg `--panel`/`--panel2`, 1px `--line` border, radius ~11px, padding 10–14px.
- **Stage card:** inset card + uppercase label (`.n`) + mono count (`.c`). **State `hot`:** border →
  `--emerald`, bg → subtle emerald gradient, .3s transition (fires when that stage emits live).
- **Metric tile:** small uppercase label over a large mono value; lift uses `--emerald`, reviews use
  `--amber`; empty state shows `—`.
- **Buttons:** primary "▶ Run Full Pipeline" (filled accent), secondary "Clear" (outline `--line`).
- **Connection badge:** green "live (SSE)" when streaming; falls back to "polling".
- **Event-stream row:** mono `kind` label + dim metadata; newest on top; grouped by `stage`.

## 5. Layout & spacing
- Max content width ~1120px (`--max`). 7-column stage grid on desktop; 2-col panel grid below.
- Compact rhythm: 8px gaps, 10–18px section margins. Density over whitespace — but avoid dead space
  below the fold on short pages.

## 6. Depth & elevation
Flat with hairlines, not shadows. Elevation = a lighter panel + a 1px border, occasionally a subtle
gradient on an active ("hot") element. No drop-shadows, no glassmorphism, no rings around raw context.

## 7. Do's & don'ts
- ✅ Monospace every number/ID/hash/handle. ✅ Dark ops surface for product + dashboard. ✅ One hue
  per semantic role (emerald=good, red=contradiction, amber=warning/review, purple=fragility).
- ❌ No dev-dark + orange. ❌ No seventh front-end column for raw document processing (it's a
  BACKEND layer under Source Systems). ❌ No inspector panel between canvas and rails. ❌ Don't
  hardcode hex literals in new components — use the `--token`s above (see §Known drift).

## 8. Responsive behavior
Stage grid collapses 7-col → 2-col under ~820px. Panels stack single-column on mobile. Mono numbers
never wrap mid-value.

## 9. Agent prompt guide
> "Build on Baltor's dark ops surface: bg `#0a0d14`, panels `#121723`/`#0e131d`, hairline borders
> `#1f2734`, ink `#e6edf6`, muted `#8aa0b6`. Inter for UI, monospace for every number/ID/hash/handle.
> Cards: 1px border, ~11px radius, compact padding. Semantic colors: emerald `#34d39a`=good/lift,
> red `#ff6b6b`=contradiction/blocked, amber `#f5a623`=warning/review, purple `#a98bff`=fragility.
> Flat + hairlines, no shadows. Instrument-panel density, not marketing whitespace."

---

## Known drift (owner-decision item — NOT resolved here)
The shipped CSS defines several tokens with **conflicting values across `web/baltor` files** — the
no-magic-values problem applied to design tokens. Convergence to one set is a brand decision (needs
owner intent), so it is flagged, not imposed.

**Live source of truth for this list:** `python3 scripts/check_design_tokens.py` (a reporter; in the
flywheel as `check_design_tokens`). Run it for the current, complete drift set — the table below is
an illustrative sample and may lag the tool.

| Token | Conflicting values seen | Documented above |
|---|---|---|
| `--bg` (dark) | `#0a0d14`, `#07090c` | `#0a0d14` (dashboard) |
| `--ink` (dark) | `#e6edf6`, `#f5f7fa` | `#e6edf6` |
| `--line` (dark) | `#1f2734`, `#262d38` | `#1f2734` |
| `--muted` (dark) | `#8aa0b6`, `#a0a9b8`, `#697892` | `#8aa0b6` |
| `--amber` | `#f5a623`, `#d9ae61` | `#f5a623` |
| `--red` | `#ff6b6b`, `#ef7272` | `#ff6b6b` |
| `--blue` | `#5aa0ff`, `#4c8df6` | `#5aa0ff` |
| `--gold` | `#e9b949`, `#d9ae61` | (not used in dark ops) |

**Follow-up status:** `scripts/check_design_tokens.py` is BUILT (a reporter, in the flywheel) — it
parses `web/baltor/*` `<style>` blocks for `--token:` defs and lists every token with >1 distinct
value, extending the No-Magic-Values discipline to CSS. It runs `--strict` (exit 1 on drift) for a
future CI gate. Remaining (await owner sign-off on the canonical palette): converge to a single
`web/baltor/tokens.css` imported everywhere, then flip the reporter to `--strict` in CI.
