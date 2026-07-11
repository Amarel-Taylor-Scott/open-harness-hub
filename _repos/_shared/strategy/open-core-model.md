# Open-Core Model — what "Open" in OpenHubForAI means

> **Name (current):** **OpenHubForAI** / `openhubforai.com`. We keep the
> high-traffic "harness" keyword but let **"Hub"** carry the breadth (a hub of many
> component types — Knowledge Corpus, Conditional, Action, Loop, …, not just
> harnesses) and **"Open"** carry this open-core split. The breadth lives in the
> tagline + the product, not in a risky rebrand.

## The line: open the protocol + engine, commercialize the governed content

The free, public, open layer is the **format and the machine that runs it**. The
commercial layer is the **capability-lifting, governed content** and the **live
service** — the things an export can't freeze. This is the same boundary the
monetization brief already draws ("the export is the commodity … recurring value is
the live/governed layer"), now stated as an open/closed product line.

| | **OPEN** (this public repo · free funnel · MIT / CC-BY) | **COMMERCIAL** (the product · subscription / metered) |
|---|---|---|
| **Protocol & spec** | `taxonomy/SPEC.md`, `schemas/`, `vocabularies/`, the **seven-primitive model**, the component/ID/hash format | — |
| **Engine** | `scripts/` — validator, `build_*`, emitters, the **foundry pipeline code** (`scripts/foundry/`), the CLI | hosted/managed runs of the same engine |
| **Logic / framework** | the gate logic, novelty, standardize, measurement *mechanism*, the design system | — |
| **Content** | **externally published/verified public knowledge** (gov agencies, standards bodies, public-domain/CC-BY) + **public-good components** (anti-human-trafficking, child-safety, humanitarian — free even as RAG/runtime) + anything a **government entity publishes via a verified OHH account** + a curated **open seed** | OHH's **verified RAG databases** & curated corpora (the verification *is* the value), **custom tools**, **runtime-heavy functions**, and the first-party components the foundry promotes |
| **Live layer** | — | **dynamic corpora** (freshness/CDC/revocation), **hosted execution** of code-executing components, signed-publisher governance |
| **On-demand** | — | **build-on-demand** fulfillment of capability-requests; **private tenant registries**; managed ingestion |

**One-liner:** *the protocol and the engine are open so anyone can author, validate,
and run components in the format; the capability-lift + governance that make a
component worth paying for stay commercial.*

## Why this split (not the alternatives)

- **Open the standard → ecosystem + credibility + the canonical index.** An open
  format/engine lets others build and publish in our shape; the Hub becomes the
  place those components are indexed and searched. "Open" is a moat *for adoption*,
  not a giveaway of the moat itself.
- **Close the content → the real moat stays paid.** The value isn't the YAML shape
  (open); it's the *measured lift*, the *provenance/signed facts/CDC*, and the
  *experience database* of what composes well. That's exactly what the
  capability-lift gate and the foundry produce — so it's what the subscription buys.
- **The public repo *is* the open core.** No relicensing needed: this repo stays
  MIT/CC-BY (engine + spec + seed). The commercial content + hosted service live in
  the product / private registries, **not** in this repo (consistent with "do not
  republish `_reference/`").

## How it maps to execution-class (already canonical)

The boundary lines up with the execution-class model
(`docs/concepts/component-taxonomy-and-stages.md`):

- **Freezable → eligible for the open seed:** `static-information` + `text-operation`
  components that are *static* (a fixed, versioned definition). Safe to export and
  self-host.
- **Live → commercial:** `code-executing` components (tool/harness/adapter/pipeline —
  need creds, sandbox, cost gates) and **dynamic** Knowledge Corpora (decay the
  moment you disconnect). These justify recurring revenue.

## How the foundry routes to each side (implemented)

`scripts/foundry/openness.py` classifies every promoted component **OPEN (free tier)
vs COMMERCIAL**, and `stage_load` stamps the `openness` tier + `basis` onto each
`index_record`. Precedence (first match wins):

0. **Public-good carve-out → FREE.** Components in a public-good domain
   (anti-human-trafficking, child-safety, humanitarian/disaster) are free, **overriding
   the paywall** — an anti-trafficking *verified RAG database* is still free. The set
   is tight + curated and deliberately **excludes** the generic ESG/forced-labor wedge.
1. **Verified public-authority publisher → FREE.** Anything a **government entity /
   public authority publishes through a verified OpenHubForAI account** is free
   (the signed-publisher path).
2. **Execution** — `code-executing` (custom tools, harnesses, adapters, pipelines)
   and **verified RAG databases** (the vector/dense retrieval OHH builds) → **commercial**.
   *(Freshness/dynamic is a separate **delivery/billing** axis — `scripts/foundry/access.py`,
   `_repos/_shared/strategy/monetization-mechanisms.md` — not an openness axis: a gov-published
   dynamic corpus is free content with a paid freshness feed.)*
3. **Verification provenance** — knowledge/rules **published or verified by an external
   public authority** (gov agency / standards body, public-domain/CC-BY) → **open**;
   content OHH curated/verified itself → **commercial**. Format/logic/eval scaffolding
   (processor, pattern, persona, rubric, benchmark) → **open**.

Demonstrated: from *one* EU source the foundry promotes the **verified RAG corpus →
commercial** and the **public-regulation grep rules → open**; an anti-trafficking RAG
database → **free** (public-good); a gov-account-published fact set → **free**.

## Resolved boundary (2026-05-28)

Not a single minimal/generous dial — a **two-axis rule** (above), confirmed with the
owner:

- **Open (free tier)** = component **definitions** + **schemas** + the
  **export/portability** capability + **externally published/verified public
  knowledge** (gov agencies, standards bodies) + logic/format scaffolding + two
  top-precedence carve-outs: **public-good components** (anti-human-trafficking,
  child-safety, humanitarian — free even as RAG/runtime) and **anything a government
  entity publishes via a verified OHH account**.
- **Commercial** = OHH's **verified RAG databases / curated corpora**, **custom
  tools**, **runtime-heavy functions** (advanced runtime imaging), dynamic corpora,
  the live layer, and build-on-demand.

Implemented in `scripts/foundry/openness.py`; widen or tighten the open seed by
adjusting the public-authority / RAG thresholds there (a one-place change).

---

*Grounds: `_repos/_shared/strategy/product-market-monetization-brief.md` (export-is-the-funnel /
live-layer-is-the-business), `docs/concepts/component-taxonomy-and-stages.md`
(execution classes + the pricing boundary), `AGENTS.md` (MIT code / CC-BY data),
`scripts/foundry/` (the engine that produces the governed content).*
