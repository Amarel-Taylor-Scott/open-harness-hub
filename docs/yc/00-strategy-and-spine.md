# 00 · Strategy & Spine (locked)

## The focus call
One company (**Teleon**), one demoable wedge (**Observer**), an explicit roadmap. A roadmap is a
strength; the two things that sink YC applications are narrower: (1) a *present-tense* "what do you do"
that tries to be three products at once, and (2) a literal holding-company cap table with separate
corps. We avoid both: **narrative breadth, structural focus.**

## The roadmap (and why this order is inevitable, not arbitrary)
**Observer → Teleon → Baltor.**
1. **Observer** — the fastest-adopted product **and** the data engine. The session data it collects
   (what got reinvented, which cheap paths won, and the human's accept/reject outcome) is exactly the
   proprietary data the platform needs. The entry product *is* the moat.
2. **Teleon** — the platform that engine becomes: run any task on the cheapest model/setup that still
   passes the user's own tests, on the user's own cloud, with an audit trail.
3. **Baltor** — the **supplementary** product: the *same* governance engine pointed at a regulated
   buyer (compliance/AML). Different go-to-market, identical tech — expansion, not sprawl.

> *"Observer gets us in and feeds the engine; Teleon is the platform that engine becomes; Baltor is
> that same engine sold to compliance."*

## Why this is real, not a slide (grounded in the repo today)
Observer is built as four seams under `src/teleon/observer/`:
- **capture** — normalizes heterogeneous AI-tool sessions into one event stream. Claude Code and Codex
  already persist sessions as JSONL on disk, so the post-session reviewer works with **zero live
  install** — we read what's already there.
- **router** — runs a taxonomy of checks, each with its own grounding and failure mode: *reinvention*
  (grounded in our index of what already exists → can ask), *footgun* (grounded in pattern rules → can
  block), *adversarial* (grounded in question templates → notice only).
- **review** — the post-session reviewer is literally the router run in batch over a finished session
  (zero live interruptions). This is the "lead with this" adoption wedge.
- **session_store** — records each finding **and** the human's outcome (accepted / reused / dismissed /
  ignored). That outcome signal is the moat a competitor with the same hooks does not have.

The "this already exists" call is a **lookup** against a grounded index (`src/teleon/knowledge/` + the
registry federation), not an LLM guess — that's what keeps it precise enough to trust.

## The honest fork (decide once, commit)
Default: **lead with Teleon/Observer** (demoable, huge horizontal market, clean roadmap). **Only** lead
with **Baltor** if its compliance traction is *real and verifiable today* — a live run that caught a
real violation **plus** a paying/committed design partner. Lead with one, never both.

## Entity note (act before submitting)
The repo carries a holding-company narrative (**"AI Done Right"** over Teleon / Baltor / Open Hubs).
For YC, present **one Delaware C-corp (Teleon)** as the operating company; keep the multi-product story
in the *narrative* only. Simplify or clearly designate the single operating entity before submission.

## Expectation reset
Application = the written form + the 1-minute video. Interview = a 10-minute Q&A + a look at the working
product, **no slides**. The deck (`03-deck.md`) is for **Demo Day and the seed raise**.

## §RULES jargon table (translate every internal term before it goes external)
| Internal | Say instead |
|---|---|
| "Teleon runs purpose" / "intent-native, eval-gated, self-adaptive compute" | "we run each AI task on the cheapest model that still passes your tests" |
| "descent brain" | "it learns the cheapest setup that still works, and re-learns as models change" |
| "capability valleys" | *(drop)* |
| "medallion pipeline (Bronze/Silver/Gold)" | "we verify data in stages — raw → checked → ready" |
| "governed context supply chain" | "we keep the facts your AI uses correct and current, and prove it" |
| "CapabilityTask / CTS / seven-primitive grammar" | "a reliable task you call instead of burning tokens" |
| "the receipt" | "an audit trail you can hand an examiner" |
| "BYO-compute" | "the AI runs on your own cloud account; we never touch your compute" |
| "lift-gated / measured lift" | "every component proves it actually helps, on your own data" |
| "reinvention guard / federation / search_all" | "we check, against a real index, whether the thing already exists" |
| `serves_truth=false`, `go_live_ready=false` | *(don't show flags — state plainly what's proven vs not)* |

**Test:** after any sentence, is the reader closer to *rebuilding* the product? If yes, you over-shared
the architecture — rewrite toward the pain and the wedge.
