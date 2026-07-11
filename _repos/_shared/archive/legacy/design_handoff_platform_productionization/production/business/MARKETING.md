# Marketing & GTM — the plan (Pass 11)

Builds on the design repo's MARKETING.md (positioning, copy) — this file is the
operational GTM: channels, plays, budget, and what gets measured. Rule: every channel
ships with its funnel events wired (BUSINESS-PLANE.md) BEFORE spend or effort scales;
no unmeasured marketing.

## Positioning (settled, don't relitigate per-channel)
- Thesis: **discovery is not trust.** Open AI building blocks are easy to find and
  unproven; AIDR turns them into governed, evidence-backed capability.
- Baltor: "They ground the answer in your corpus — even if the corpus is wrong.
  We verify the corpus." (vs RAG/Contextual-class tools)
- Teleon: "Define the outcome. We prove the rest."
- Hubs: "Open to use. Governed to trust." — registry front door, container product.

## Channel plan (in order of adoption; CAC ≈ $0 until #5)

1. **The hub content engine (SEO, programmatic).** 21 registries × every entry =
   indexable pages with real utility (install commands, provenance, eval scores).
   This is the moat channel: nobody else's directory pages carry receipts.
   Measure: `discover` events per hub; entries indexed.
2. **Launch events.** Every private→live hub flip is a launch (Show HN, Product Hunt,
   r/selfhosted, MCP/agent communities). 12 private-bench hubs = 12 staged launches —
   a year of launch cadence already sitting in the repo. Baltor/Teleon get their own.
   Measure: visitor spike, signup conversion per launch.
3. **Container distribution as marketing.** Images on ghcr + Docker Hub with
   SBOM/cosign badges; READMEs are landing pages; `docker pull` is the CTA. Awesome-*
   lists, MCP server directories, agent-tool catalogs.
   Measure: pulls, verified-deployment handshakes (S-E).
4. **Founder-technical content.** The receipts/provenance thesis writes itself:
   held-out conflicts, verified-corpus vs grounded-answer, "your AI's context is
   stale and here's the proof." 1–2 posts/mo, cross-posted (blog → HN → newsletter).
   Measure: `engage` events from content referrers.
5. **First paid experiment (gated).** Only after organic baseline is measured; needs
   its own pro-forma line (channel, budget cap, CPL target) before a dollar moves.

## The demo IS the marketing
The guided demos and Live Run consoles are the conversion engine — every marketing
page routes to "watch it run" (engage event), not a form. A/B via OHExp (shipped):
hero copy, CTA, demo-first vs docs-first. Exposure/conversion already have a sink.

## Budget
$0–100/mo until Stage 2 (domains-at-launch + occasional boosts). Paid channels enter
the pro-forma only with a CPL hypothesis and a kill threshold.

## What gets reported (weekly, from events — no vanity)
discover → engage → signup → activate per realm · launch deltas · pulls/handshakes ·
top content referrers. If a number can't come from the events plane, it doesn't go in
the report.
