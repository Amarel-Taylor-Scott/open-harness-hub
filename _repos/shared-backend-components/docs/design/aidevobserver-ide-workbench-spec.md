# AIDevObserver IDE — workbench mode spec (owner design direction, 2026-07-01)

> **Status:** owner-provided design critique adopted as the target spec for the `/ide` view of
> `web/aidevobserver`. Executes under the Northstar design law (DESIGN-BIBLE; shared kit; no placeholders).
> Core correction: **when the user enters IDE mode, the app shell disappears — the IDE becomes the product.**
> References: VS Code workbench (layout), Claude Code (terminal interaction), Open WebUI/LiteLLM (model
> config), Langfuse (traces/review), vLLM+Grafana (runtime metrics pages only — never the IDE layout).

## 1. Two modes

- **Dashboard mode** (unchanged): app sidebar + Dashboard/Review/Sessions/Findings/Reports/… (Langfuse-like).
- **IDE/workbench mode**: VS Code-style panes — activity bar · file explorer · editor tabs · interactive
  terminal · status bar. App sidebar hidden by default (collapsible back); fullscreen is first-class.

```
┌────────────────────────────────────────────────────────────────────┐
│ AIDevObserver · workspace-name                          ⚙  ⛶  Exit │
├────┬────────────────┬──────────────────────────────────────────────┤
│ ◎  │ Explorer        │ editor tabs / content                        │
├────┴────────────────┴──────────────────────────────────────────────┤
│ Terminal ($ interactive, Claude Code-like)                          │
├────────────────────────────────────────────────────────────────────┤
│ Observer ready | models: Kimi, GLM | harness: OpenCode | search: on │
└────────────────────────────────────────────────────────────────────┘
grid-template-columns: 48px 280px minmax(0,1fr) [drawer 340px];
grid-template-rows: 34px minmax(0,1fr) 220px 24px;  /* all panes resizable + hideable */
```

## 2. The right rail is REMOVED by default

Models/harnesses/benchmark-lab toggles/“Compose supervised run”/“Save session URL” move into a **gear
lightbox** (tabs: Models | Harnesses | Intelligence | Session | Advanced) with compact rows
(`☑ Kimi Code · kimi-k2.7-code · ● ready`), not cards. Current selections surface as **clickable status-bar
chips** (each opens its settings tab). A right **drawer** may appear only for live run details
(plan/diffs/trace/review) and must be hideable. Quiet healthy states (`●`), loud error states
(`disconnected`, `missing key`).

## 3. Terminal = primary interaction surface

Interactive like Claude Code, not a log block: focus/cursor, typed commands + natural-language tasks,
streaming output, approve/cancel (`Apply changes? [y/N]`), history, Ctrl+C, tabs, clear, resize. "Compose
supervised run" becomes typing in the terminal, a compact `Run` in the top bar, or the command palette —
never a giant CTA card.

## 4. Remove / relocate

- Page heading + explainer copy ("Browser control room…") → dashboard/welcome tab only.
- Global floating `Refresh` → per-pane actions (Explorer refresh · terminal restart/clear · models refresh).
- Oversized `READY` badges → settings modal only; reserve badges for problems.
- Wrapping filenames → `text-overflow: ellipsis; white-space: nowrap` in the explorer.

## 5. Shortcuts + model lanes

`Ctrl/Cmd+B` explorer · `` Ctrl+` `` terminal · `Ctrl/Cmd+,` settings · `F11` fullscreen · `Esc` closes
modal/drawer · `⌘K` palette. Model lanes stay the fleet: deterministic · Kimi K2.7-code · GLM 5.2 (+ Gemma 4
batch lane where exposed); harnesses: OpenCode build loop · Claude Code · Codex CLI · Aider.

**Acceptance:** entering `/ide` shows NO app sidebar, NO page heading, NO right rail; gear opens the
lightbox; status bar shows live chips; terminal accepts typed input end-to-end; all panes hide/resize;
0 console errors under the showcase.
