# ADR 0010 — Path-universe explorer: expand any implementation into its decision graph + branches

## Status
Proposed (2026-07-04, owner-raised). Recommend building — it is the **capstone assembly** of what this session
already built, plus two well-scoped new pieces. Fits PMF (it productizes the multi-path thesis; core, not breadth).

## Context
Owner wants a NEW project tool: take **any project / algorithm / notebook** (a single working path), use LLMs +
tools to **generate all the other ways to accomplish the same task**, represent them as a **graph of decisions +
associated code**, and **materialize them in GitHub/GitLab as branches/forks**. Assessed reuse-first.

## Decision
1. **This is ~80% assembly of existing pieces — do NOT rebuild the engine.** It composes:
   - ADR 0008 — the decision-graph / path-universe generator (the constrained option grid + selector).
   - ADR 0007 — the primitive store's git-like fork / branch / merge / supersede (each path is a branch).
   - the generic executor (ADR 0007) — runs each generated path by ref.
   - `parallel_paths` / `run_path_bakeoff` — race the paths on the same input, rank by receipts, keep losers as
     labelled fallbacks (the multi-path law).
   - ADR 0009 — Fable-as-compiler (generate/critique the alternative code; never the only runtime).
   - the git-branching plane (Omnigraph, or real git via our push machinery).
2. **Two genuinely NEW pieces to build:**
   a. **DECOMPOSE front-end** — an LLM (Fable-as-compiler) ingests an existing implementation and extracts its
      decision points (preprocess · algorithm · library · params · postprocess · I/O) into the decision-graph
      skeleton. This is the *reverse* of ADR 0008 (which starts from a spec); this starts from working code.
   b. **MATERIALIZE back-end** — each generated path → associated code → stored as a fork/branch in the
      primitive store AND/OR pushed as a real **git branch/fork** (GitHub via the session's push machinery;
      GitLab if the self-hosted substrate lands).
3. **Flow:** single path in → decompose → decision graph → path universe (constrained product) → generate code
   per path → git branches/forks → bake-off → optimal chosen + graphed, losers kept. Each path is a candidate
   primitive route (`serves_truth=false` until its receipts pass).
4. **Home:** the SAME repo as ADR 0008 — `aidoneright-decision-graph` — covering BOTH directions: **spec →
   universe** and **implementation → universe**. One tool, two front doors.

## Consequences
A genuinely helpful, marketable dev tool that IS the multi-path thesis productized — built mostly from existing
components, with two well-scoped new seams (decompose, git-materialize). Because it's the core thesis (not a new
vertical), it passes depth-before-breadth as tooling that serves the whole portfolio.

## Enforcement / links
ADR 0007 (store forks + executor), 0008 (path universe), 0009 (Fable compiler); `parallel_paths` /
`run_path_bakeoff`; the git push machinery used across this session.
