# Self-review — videos, logs, screenshots, and persona journeys (2026-06-09)

Reviewer: the build loop itself (machine sweep of every console/network log + visual inspection of
key stills + 6 scripted customer-persona journeys with video). Everything below is evidence-linked.

## 1. Artifact review (the existing videos/logs/stills)

**Healthy:**
- 16/16 surfaces load with **0 page errors, 0 overflow, 0 dead links** (after the Pass-7/8 fixes).
- The portal video shows the secrets policy WORKING: raw key illegible (blur) in
  `portal-06-mint-key-blurred.png`, key list renders prefix-only (`ak_openharne…`), passphrase
  never appears in any artifact (proof-gated).
- Mobile (390px) renders cleanly on the launch sites, with the honest "Preview build — temporary
  URL, not production hosting" disclaimer visible.
- The Demo Control Tower presents honest status chips (active/candidate/internal), a numbered
  demo script, and a caveats section — exactly what a reviewer needs.

**Issues found by review:**
1. **Toast overlap bug (real UI defect):** in `portal-06-mint-key-blurred.png` two toasts render
   on top of each other at bottom-center ("Key minted…" colliding with "Account activated…"),
   producing garbled text. Fix: stack toasts vertically or queue them (web/harness-hub app.js
   toast implementation).
2. **Systematic favicon 404:** 13/16 surfaces log exactly one console error — `GET /favicon.ico
   404`. One-line fix per shared layout (inline `<link rel="icon" href="data:,">` or a tiny SVG
   favicon in the shared kit). Low severity, but it pollutes every console log and masks real
   errors in monitoring.

## 2. Persona journeys — 6 customer types, recorded (videos/persona-*.mp4)

| Persona | Result | Video |
|---|---|---|
| Dana — compliance lead, fintech (Baltor buyer) | 9/10, 1 friction | persona-compliance-lead-fintech.mp4 |
| Marco — AI platform engineer (Teleon buyer) | 7/8, 1 friction | persona-platform-engineer-agents.mp4 |
| Priya — solo agent developer (OHH user) | 11/11 **smooth** | persona-agent-developer-builder.mp4 |
| Wei — OSS hub publisher | 6/8, 2 frictions | persona-oss-hub-publisher.mp4 |
| Sam — investor with 10 minutes | 8/8 **smooth** | persona-investor-demo-reviewer.mp4 |
| Alex — security reviewer | 12/12 **smooth** | persona-security-reviewer.mp4 |

**The smooth journeys matter:** the security reviewer found every gate failing closed — anonymous
`/account/keys` gates instead of leaking, the realms projection exposes metadata only (the
inverted leak-probe found no account/credential/session material), and a wrong-password login
returns a generic "rejected" (no account enumeration). The investor path through the Control
Tower hit only honest statuses and real links.

**The 4 real frictions (each has a screenshot `friction-<persona>-*.png`):**
1. **Baltor buyer can't see the regulated-domain proof point** — no sanctions/OFAC/CFPB anchor
   visible on the buyer-facing pages (`friction-compliance-lead-fintech-10.png`). The repo HAS
   the live OFAC proof; surface it on the Baltor app/site as the compliance proof point.
2. **Teleon landing has no docs/API/quickstart path** for an engineer ready to integrate
   (`friction-platform-engineer-agents-04.png`). Add a docs/quickstart CTA (even to a local
   OpenAPI page — ties into the identity-service OpenAPI item already queued).
3. **Publisher can't find a publish/submit path** on the OpenHarnessHub prototype landing
   (`friction-oss-hub-publisher-06.png`) — it may exist behind the account console, but a
   publisher persona scanning the page doesn't see it. Surface "Publish" in the top nav.
4. **No "submissions land in review, never auto-active" statement** visible to a publisher
   (`friction-oss-hub-publisher-08.png`) — this is a stated law of the registry
   (candidate≠active); saying it on the publish surface builds exactly the trust the persona
   needs. ("Discovery is not trust" IS present — that probe passed.)

**Runner honesty note:** the first run reported 8 frictions; 4 were a runner false positive
(Playwright returns a null response for same-document hash navigation) — fixed in
`persona_journeys.mjs` and re-run before this report. The page-content probes had passed all
along, which is how the false positives were caught.

## 3. Next use-case wave (ideation source, governed)

The owner's side research repo (`/home/username/code_projects/common-capability-actions`,
~250 CapabilityAction entries with sources + quarantine discipline) is the right feed for the
next persona wave: map high-frequency actions (invoice extract, ticket summarize, queue worker
retry/DLQ, MCP connection test, …) onto NEW personas (support lead, RevOps, data engineer,
SRE) and script their journeys against the Teleon/Baltor surfaces as those capabilities land.
Per the law: that catalog is candidate intelligence — discovery ≠ trust, nothing auto-activates.

## 4. Priority fix queue (from this review)

1. Toast stacking bug (visible in the flagship portal video).
2. Surface the OFAC/sanctions proof point to the Baltor buyer journey.
3. Teleon docs/quickstart CTA.
4. Publish path + "review-queue, never auto-active" statement on the hub surface.
5. Shared favicon (kills 13 console errors).
