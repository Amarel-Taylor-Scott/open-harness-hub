---
license: CC-BY-4.0
tags:
- ai-launch
- creative
- cross_industry
- experimental
- icp
- launch
- open-harness-hub
- positioning
- pricing
- product-hunt
- retrieval
- saas
- software
- verification
task_categories:
- text-classification
- text-retrieval
size_categories:
- n<1K
language:
- en
pretty_name: SaaS / micro-SaaS / AI-app launch playbook reference
---

# SaaS / micro-SaaS / AI-app launch playbook reference

<!-- Generated from OpenHubForAI manifest `knowledge-pack/saas-launch-best-practices` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Reference pack of (composite educational) extracts covering the
most-cited public guidance on SaaS launches, distilled from
founder-written posts, YC essays, IndieHackers founder stories,
Product Hunt launch retrospectives, and 2022-2026 vertical-SaaS
case studies.

**Positioning & messaging:**
 - April Dunford's *Obviously Awesome* positioning canvas:
   competitive alternatives, unique attributes, value, target
   customers, market category.
 - "Made for X" tagline pattern.
 - The 5-second clarity test.
 - The Jobs to Be Done (JTBD) framing.
 - Lenny Rachitsky's "your tagline is your product" essays.

**Pricing:**
 - 9-3-1 pricing pattern (cheap / target / premium).
 - "Pricing page is a feature" — show pricing on landing or 1
   click away.
 - The "contact sales" trade-off: appropriate only for
   enterprise (>$100K ACV); friction for self-serve.
 - Trial conversion patterns: 14-day free with CC vs no CC;
   freemium → paid upgrades.
 - Per-seat vs per-usage vs per-outcome pricing trade-offs.

**ICP / customer specificity:**
 - "Specific is the new big" (Justin Jackson).
 - The "five whys" of ICP definition.
 - ICP red flags: "everyone", "all sizes", persona-kitchen-sink.

**Demos & proof:**
 - Live demo > video demo > screenshots > "request demo" hierarchy.
 - Demo video length: <90 seconds first-touch, <3 minutes deep-dive.
 - "Show, don't tell" with annotated screenshots.
 - Loom-style asynchronous founder demos.

**Product Hunt launch best practices (2024-2026):**
 - Launch day: Tuesday or Wednesday, 12:01am PT.
 - Avoid: Mondays (CEO returns from weekend), Fridays (low
   engagement), week of major industry conferences.
 - First-comment-as-maker convention.
 - Mobilization: pre-launched comment subscribers, hunter +
   maker pre-coordination.
 - Visual asset: GIF demo + 3-5 screenshots + thumbnail with text
   overlay.
 - Tags: 3-5 maximum, specific category fit.
 - Upvote rules: Product Hunt-enforced anti-gaming policies.
 - Top-of-day vs daily winner: PH algorithm weights early
   engagement.

**IndieHackers conventions:**
 - Revenue transparency (MRR / ARR / cum revenue).
 - Founder-story angle: technical + business + personal.
 - Engagement: respond to every comment in first 24 hours.

**Show HN conventions:**
 - "I built X because Y" hook in title or first line.
 - Working link, not a marketing page.
 - Technical detail in the post or comments.
 - Don't post on behalf of a company you don't run yourself.

**AI-specific 2024-2026 launch lessons:**
 - "Custom GPT" wrappers struggle — model commodity, no moat.
 - High-stakes verticals (legal, medical, financial) require
   accuracy / evaluation / human-in-the-loop disclosure or face
   trust collapse on launch.
 - "Powered by Claude / GPT" is not a differentiator; the moat
   is in: workflow integration, data, evaluation harness,
   domain knowledge, network effects.
 - Vertical AI is outperforming horizontal AI in 2026 (per
   Bessemer's Vertical AI report).
 - Pricing AI products: hybrid per-seat + per-usage emerging
   standard; pure-token-pricing struggles for SMB.

Composite educational extracts. Not a substitute for actual
founder mentorship or paid GTM consulting.

**Industries**: software, creative, cross_industry
**Capabilities**: retrieval, verification
**Modalities**: text
**Freshness**: dated
**Trust boundary**: local

## Content types (leaf vocabulary)

- `rag_doc`
- `citation_edge`

## Files

| path | format | schema |
|---|---|---|
| `data/saas-launch-pack/positioning-and-messaging.jsonl` | jsonl | — |
| `data/saas-launch-pack/pricing-patterns.jsonl` | jsonl | — |
| `data/saas-launch-pack/icp-frameworks.jsonl` | jsonl | — |
| `data/saas-launch-pack/demo-and-proof.jsonl` | jsonl | — |
| `data/saas-launch-pack/product-hunt-conventions.jsonl` | jsonl | — |
| `data/saas-launch-pack/indiehackers-conventions.jsonl` | jsonl | — |
| `data/saas-launch-pack/show-hn-conventions.jsonl` | jsonl | — |
| `data/saas-launch-pack/ai-launch-2024-2026-lessons.jsonl` | jsonl | — |

## Provenance

- **sources**: April Dunford, Obviously Awesome (2019), Lenny Rachitsky, Lenny's Newsletter (2021-2026), Justin Jackson, MegaMaker / Transistor blog, Product Hunt help center + 2024-2026 launch retrospectives, IndieHackers founder interviews (2018-2026), Bessemer Venture Partners, Building Vertical AI (Jan 2026), YC essays + Startup School, Composite distillation; no per-source verbatim text
- **collected_through**: 2026-05-15

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/saas-launch-best-practices.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{saas-launch-best-practices_open_harness_hub,
  title  = {SaaS / micro-SaaS / AI-app launch playbook reference},
  author = {OpenHubForAI contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/saas-launch-best-practices},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/saas-launch-best-practices`.
