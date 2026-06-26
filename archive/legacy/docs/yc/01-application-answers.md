# 01 · YC Application Answers (Teleon / Observer)

> Drafts for **Teleon**, jargon-stripped, honest. `[FILL IN]` = founder-specific. Keep every answer
> tight — YC partners skim thousands. Numbers labeled **measured** / **representative** / **proposal**.

**Company name:** Teleon *(apply under the product brand you own — not the "AI Done Right" holding name).*

**Company URL:** `[FILL IN — e.g. teleon.dev]`

**What does your company do? (≤50 chars):** `Catches wasted spend in your AI coding sessions`
*(alternates: `Runs AI tasks on the cheapest model that works` · `Cut your AI bill without losing
quality`. Write 20, test one on a non-technical friend.)*

**1-minute founder video:** see `02-one-minute-video.md`.

**What is your company going to make?**
> Teleon cuts what companies spend on AI. Our first product, Observer, reviews your AI coding sessions —
> the work you do with tools like Claude Code, Cursor, and Codex — and shows you three things you can't
> see today: where you burned tokens for no reason, where the AI rebuilt something that already exists
> (a public library, or a module already in your own codebase), and where a cheaper model would have
> passed just as well. It runs after a session as a report, and during a session as the occasional
> well-timed nudge. The data Observer collects — including whether you accepted or dismissed each
> finding — is what trains the platform underneath it: an engine that, for any task you describe in
> plain English, finds the cheapest model-and-setup that still passes your own tests, and keeps it
> cheapest as new models ship. The AI runs on your own cloud account; we never touch your compute. We
> decide which cheap path is safe, and we prove it.

**Where do you live now / based after YC?** `[FILL IN]` — *commit to relocating to SF for the batch;
vague / "remote" answers read as not serious.*

**Founders / team:** `[FILL IN names, roles, contact, LinkedIn]`. **Who writes code / technical
background:** `[FILL IN]`. *If solo, say so directly and confidently. Strongest capability evidence is
what's already built — name it concretely: the Observer pipeline (capture → session store → review →
router) that reads Claude Code / Codex sessions with zero install, the grounded index
(`src/teleon/knowledge`) that makes "this already exists" a lookup not a guess, and the reinvention
guardrail's precision discipline (silent on genuinely-novel work).*

**How long have the founders known / worked together?** `[FILL IN]`

**Why this idea? Domain expertise? How do you know people need it?**
> `[FILL IN — your true "why us"; see 05-stories.md §5.1]`. The need isn't speculative: AI tool spend
> now runs roughly **$200–$600 per engineer per month** `[verify your own current figure]`, far higher
> with agentic tools, and a large share goes to tasks a cheaper model would pass and to rebuilding code
> that already exists. `[FILL IN the specific moment you saw this — a session that burned $X; an agent
> that rebuilt auth a fifth time.]`

**How far along are you?** *(grounded in the repo — what is actually implemented today)*
> - **Built:** Observer's full pipeline — *capture* (normalizes Claude Code / Codex sessions, which are
>   already JSONL on disk, into one event stream → the reviewer needs **zero install**), *router* (a
>   taxonomy of checks: reinvention, footgun, adversarial — each grounded differently), *review* (the
>   router run in batch over a finished session → the non-invasive report), and *session_store* (records
>   each finding **and** the human's accept/reject outcome — the proprietary signal). Plus a grounded
>   index of what already exists, so the "you're reinventing this" call is a lookup, not an LLM guess.
> - **Measured (our own demo lanes):** cheaper-path savings of **~47% on document extraction** and
>   **~86% on enrichment** vs always using the expensive default. *These are measured on our lanes and
>   are representative until run on a customer's own eval data.*
> - **Representative example:** a session re-reading one file burned ~320k unnecessary tokens — the
>   cheaper path is ~96% less. *(illustrative, not a customer measurement.)*
> - **Honesty gate:** we keep an automated "is this ready for production?" check that currently reads
>   **not yet** — we show it; it's a trust asset, not something to hide.
> - **Pre-submission task:** a numeric false-positive rate for the reinvention call on real developer
>   sessions (the harness proves the *discipline* — silent on novel work — today; the *number* needs
>   real runs; see `08-pre-submission-checklist.md`).
> - `[FILL IN: design partners, pilots, waitlist — anything real.]`

**How many users / revenue?** `[FILL IN — real numbers only. One true sentence ("N devs ran it on real
sessions; it caught M reinventions a senior dev confirmed; K said it found something they'd have
shipped") beats any projection. No "1,000 users" if it's 1,000 installs.]`

**Who are your competitors, and what do you understand that they don't?**
> AI-usage logging tools (LangSmith, Helicone, PromptLayer) record what your AI did; code-review tools
> review the finished code. Neither judges *how the AI was used* — whether it reinvented something
> already solved, or took an expensive path a cheaper one would pass. The agent platforms (Cursor,
> GitHub Copilot, Codex, Devin, Replit) store and run code; none govern whether the result is correct,
> cheaper, or safe — and they're incentivized to sell *more* usage, not less. Two things make our call
> precise instead of a guess, and both compound: a **grounded, continuously-updated index of what
> already exists**, and an **accept/reject memory** that learns winning cheap paths from real sessions.
> Same telemetry everyone can log; opposite purpose — they watch, we coach and cut cost.

**How will you make money? How big?** *(pricing = proposal)*
> Free, low-friction session reports as the funnel. Paid: a hosted service and a self-hosted version for
> teams that want the live, enforced guardrail and the savings — priced on active capabilities plus a
> share of the savings, **never on compute** (the AI runs on their cloud). The market is every team with
> a growing AI bill; at $200–$600+/engineer/month today and rising, even a single-digit-percent cut is a
> large, defensible line item.

**Category:** Developer tools / AI infrastructure. `[confirm against the form's list]`

**If you had other ideas you considered, list them:**
> `[FILL IN — 2–3 max, 2 sentences each. The RIGHT place to show range without losing focus: "An engine
> that picks the cheapest passing model for any task — this became Teleon's core. A product that keeps
> the facts enterprise AI uses correct and provable for compliance — our planned supplementary product,
> Baltor." Framed as considered directions, this signals vision, not scatter.]`

**Equity / incorporation:** `[FILL IN status, cap table, money raised. Present ONE Delaware C-corp
(Teleon). Simplify the "AI Done Right" holding/multi-entity structure first, or designate the single
operating company — see 00-strategy-and-spine.md §Entity note.]`

**Most impressive thing you've built or hacked (incl. non-computer systems):** `[FILL IN — one specific
story; not the startup itself; cleverness > prestige.]`

**Something surprising / amusing you discovered:** `[FILL IN — e.g. how much of a real AI session is
spent re-reading the same file, or rebuilding something the team already had.]`

**How did you hear about YC?** `[FILL IN honestly.]`
