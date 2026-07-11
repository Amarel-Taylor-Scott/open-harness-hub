# Cross-surface consistency contract — the follow-up for Claude Design

> Companion to `START-HERE.md`, `_repos/shared-backend-components/docs/DESIGN-BIBLE.md`, and the two briefs. This is the enforceable rulebook for the ONE
> thing that makes five separate surfaces feel like a single product family: they share the SAME header, footer,
> logged-in shell, layout skeletons, and primitives, and differ ONLY by accent and copy. When you build or restyle
> ANY surface (AIDevObserver first, then the others), every rule here holds. serves_truth=false.

## 0. The one law

Every surface is the SAME shared kit. Per surface you change **exactly two things**: the **accent** (`--accent`)
and the **copy**. You NEVER: fork a kit component, add a second CSS system, hand-roll a header/footer/layout, or
invent a spacing or type scale. If a component genuinely needs a change, change it **in the kit** (it propagates to
all five surfaces) and call that out in the integration handoff — that is the single design law.

## 1. The five surfaces + their accents (the ONLY thing that varies)

| Surface | accent `--accent` | what it is |
|---|---|---|
| **AI Done Right** | `#5a6b87` | parent / portfolio hub |
| **Teleon** | `#6d5ef0` | the runtime |
| **Baltor** | `#0e7c86` | governed context |
| **AIDevObserver** | `#b25fd6` | AI-usage review |
| **OpenHubForAI** | `#3b6fd4` | the open store |

Set it ONCE on the surface scope wrapper; everything inside reads `var(--accent)`:
```jsx
<div className={'oh dir-s theme-' + theme + ' oh-site'} style={{ '--accent': ACCENT }}> … </div>
```
**ONE accent per surface — this is the rule that breaks today.** Every page of a surface uses the SAME `--accent`;
never mix accents within a surface (a marketing home and an internal browser on the same surface must match). The
values above are the canonical intent; read the surface's existing `--accent` (its scope wrapper / kit tokens) and
keep it identical across all of that surface's pages. Light theme + Inter + mono are global — never re-themed per page.

## 2. The standard HEADER — `OhTopBar` (identical on every marketing / no-sidebar page)

One header, one structure: **logo (left) · nav · theme toggle + sign-in + primary CTA (right)**. A "Demo" link is
appended automatically. Never build a bespoke top bar.
```jsx
<OhTopBar brand={BRAND} nav={[['How it works','/how'], ['Pricing','/pricing']]}
          cta={{ label: 'Open the app', href: '/app' }} signInHref="/signin"
          theme={theme} onToggle={onToggle} />
```
RULES: same height + paddings (`.ohs-top`); logo = `brand.glyph` + `brand.name` + `brand.tld`; nav is `[[label, href]]`;
ALWAYS a theme toggle and a single **primary** CTA (`oh-btn--primary oh-btn--sm`). Only the nav labels + the CTA copy
differ between surfaces.

## 3. The standard FOOTER — `OhFooter` (identical on every marketing page)

Brand block (logo + tagline) + columns of links. **The last column is ALWAYS "Family"**, linking to the other four
surfaces — that cross-link is how the family reads as one company.
```jsx
<OhFooter brand={BRAND} tagline="AI-usage review · part of AI Done Right"
  cols={[
    ['Product', [['How it works','/how'], ['Pricing','/pricing'], ['Trust','/trust']]],
    ['Family',  [['AI Done Right ↗','../context-is-everything/...'], ['Teleon ↗','../teleon/...'],
                 ['Baltor ↗','../baltor/...'], ['OpenHubForAI ↗','../openhubforai/...']]],
  ]} />
```
RULES: every marketing page ends with `OhFooter`; tagline + columns are per-surface copy; the structure + the Family
column are invariant.

## 4. The standard LOGGED-IN SHELL — `OhLayout variant="sidebar"` (every app uses the SAME shell)

Left sidebar (logo top · nav · foot with a back-link + theme toggle), main content. **No top bar inside the app.**
Every logged-in product — AIDevObserver, the Teleon Control Tower, the Baltor portal, the OpenHubForAI account —
uses this identical shell.
```jsx
<OhLayout variant="sidebar" brand={BRAND}
  sidebar={[['/app','◉','Review'], ['/app/sessions','≡','Sessions'], ['/app/settings','⚙','Settings']]}
  route={route} isActive={isActive} foot={foot} theme={theme} onToggle={onToggle}>
  {screen}   {/* every screen starts with <OhPageHead/> */}
</OhLayout>
```
RULES: sidebar nav is `[[href, glyph, label]]`; the active item highlights (pass `route` + `isActive`); the foot holds
the theme toggle; the index route uses an exact-match `isActive` so the first item is not always-on. Same glyph style,
same widths across all apps.

## 5. The LAYOUT SKELETONS — `OhLayout` (pick ONE per page; never hand-roll a layout)

| `variant` | use for | composes |
|---|---|---|
| `sidebar` | the logged-in app | `OhAppShell` (left sidebar + main) |
| `no-sidebar` | marketing pages, wide tables / browsers | `OhTopBar` + content + `OhFooter` (full width) |
| `one-col` | docs, settings, simple forms | `OhTopBar` + centered 820px column + `OhFooter` |
| `two-col` | content with a sticky aside | `OhTopBar` + main + `aside` + `OhFooter` |

RULE: every page declares its shape through ONE `OhLayout` variant. There is no other way to lay out a page.

## 6. The PRIMITIVES catalog (compose these; never recreate them)

- **Chrome:** `OhTopBar`, `OhFooter`, `OhAppShell`, `OhLayout`.
- **Marketing sections:** `OhHero` (eyebrow + title + lede + ctas + optional aside), `OhSection` (label + title + body
  + children), `OhFeatures` (a 3-up card grid from `[[glyph, title, desc], …]`), `OhBand` (a centered CTA strip).
- **App:** `OhPageHead` (eyebrow + title + sub + actions — **every app screen starts with this**), `OhRollup` (a row
  of stat cards from `[[label, value], …]`), `OhTable` (the sortable, click-through data table — **every list/table is
  this**, never a hand-built `<table>`).
- **Atoms:** `oh-card`, `oh-btn` (`--primary` / `--ghost` / `--sm`), `oh-badge`, `oh-pill`, `.mono`.
- **Shared component patterns:** the AIDevObserver **finding card** and the **status badge** (live/partial/gap green/
  amber/red) must look IDENTICAL wherever findings or statuses appear, on any surface.

RULE: if you need a building block, it is almost certainly one of these. Compose; do not invent.

## 7. The PAGE SCHEMES (the only five page shapes)

- **A — Marketing:** `OhLayout no-sidebar` → `OhHero` → `OhSection`×N (each with `OhFeatures`) → `OhBand` → footer.
- **B — App view:** `OhLayout sidebar` → `OhPageHead` → optional `OhRollup` → content (`OhTable` / cards / finding cards).
- **C — Form / settings:** `OhLayout one-col` → `OhPageHead` → an `oh-card` with inputs.
- **D — Table / browser:** `OhLayout no-sidebar` → `OhPageHead` → a facet rail + `OhTable` (+ optional card-grid toggle).
- **E — States:** every data view renders **empty / loading (skeleton) / populated / error**, treated the same way
  everywhere (empty = a one-line prompt + an action; loading = skeleton rows/cards; error = the message + retry).

## 8. Consistency checklist (verify before any surface is "done")

- [ ] header is `OhTopBar` (same structure); only logo + nav + CTA copy differ
- [ ] footer is `OhFooter` with a **Family** column linking the other four surfaces
- [ ] the logged-in app is the `OhLayout sidebar` shell (logo top · nav · theme-toggle foot)
- [ ] every page is exactly one `OhLayout` variant — no hand-rolled layout
- [ ] only `--accent` + copy differ from the other surfaces (same tokens, type scale, spacing)
- [ ] finding cards, status badges, and tables look identical across surfaces
- [ ] empty / loading / error states are present and consistent
- [ ] light theme, Inter UI font, mono for code; 0 console errors; **no forked kit component**

## 9. The follow-up prompt (paste this into Claude Design after the first build)

> Apply the cross-surface consistency contract (CONSISTENCY-CONTRACT.md). Keep the SAME shared kit across every
> surface: the `OhTopBar` header (logo · nav · theme toggle · one primary CTA), the `OhFooter` footer (brand + a
> "Family" column linking the other surfaces), and the `OhLayout sidebar` shell for every logged-in app (logo top,
> nav with active highlight, theme-toggle foot). Lay out every page with ONE `OhLayout` variant (sidebar / no-sidebar
> / one-col / two-col) — never hand-roll a layout. Use only the kit primitives (`OhHero`, `OhSection`, `OhFeatures`,
> `OhBand`, `OhPageHead`, `OhRollup`, `OhTable`, the finding card, the status badge); do not invent components or a
> second CSS system. Each surface differs ONLY by its accent and copy: AI Done Right `#5a6b87`, Teleon `#6d5ef0`,
> Baltor `#0e7c86`, AIDevObserver `#b25fd6`, OpenHubForAI `#3b6fd4`. Every data view needs empty / loading / error
> states. Output one self-contained HTML per surface; verify by clicking through with 0 console errors.
