# YC Context & Agent-Infra Landscape — June 2026 (verified)

Four adversarial research passes (2026-06-11): Kaelio/ktx deep-dive · YC "context for AI"
sweep (~45 companies, batches W20→W26 verified on YC directory pages) · YC agent-infra/
verification sweep (~50 companies) · IJFW. Every batch claim was verified against
`ycombinator.com/companies/<slug>`; funding against press. Owner ask: "research KTX and any
YC backed company that is around context or tangentially similar."

## Headline: the white space holds — and now has a clock

**No YC company (through W26) does continuous verification + portable signed receipts +
governed promotion of context to truth status.** The market splits into movers (Airbyte,
Firecrawl), rememberers (Mem0, Zep, Hyperspell), retrievers (Exa, Onyx, Morphik), parsers
(Reducto, Extend), analytics-truth (Kaelio, Honeydew, Lopus), watchers (The Context Company,
Laminar), CI-gaters (Openlayer, Braintrust*), perimeter/identity (Clam, Agentic Fabriq,
Multifactor), and red-teams (Casco, General Analysis). The fragments closest to our rail:
Zep's bi-temporal fact invalidation (mechanism, no governance), Diligent's audit trails
(governance, no generality), Openlayer/Braintrust CI gates (promotion of code versions, not
facts), HumanLayer approvals (human gates, no evidence ledger). Research literature is ahead
of the market (PROV-AGENT, arXiv 2508.02866; "Tool Receipts, Not Zero-Knowledge Proofs,"
arXiv 2603.10060) — validation AND a countdown. (*Braintrust = non-YC, $80M B, named for
gravity.)

YC itself sees the gap: 41.5% of W26 is agent plumbing, framed as "who can act, what they
can touch, and how you prove it happened correctly" — but every funded attack is perimeter,
identity, or red-team. The 2025–26 consolidation wave (Langfuse→ClickHouse, Helicone→Mintlify,
Traceloop→ServiceNow, Context.ai→OpenAI, Invariant→Snyk, Prompt→SentinelOne, Lakera→CheckPoint,
Trieve→Mintlify, Quotient→Databricks rep.) says standalone observability/evals/security are
features, not companies — assurance must be a RAIL, which is the thesis.

## Kaelio ktx — the deep-dive verdict (closest "context layer" sibling)

Technical: own deterministic SQL planner ("aggregate locality" CTEs kill fan/chasm traps;
sqlglot only for dialect transpile), 11 MCP tools (verified from the repo's test snapshot),
RRF-fused 3-lane retrieval (FTS5 + embeddings + token overlap), LLM-agent reconciliation over
a deterministic write index with a 7-action labeled diff vocabulary, `canonical_pins`,
`.ktx/ingest-evidence` local evidence dirs. Commercial: YC X25, ~$500K YC-standard, 8 people,
2-committer bus factor, open-core (governance/approvals/SSO/audit = paid ktx Cloud),
logo wall unverified as revenue. Trajectory: 11 minor releases in 21 days; admitted gaps =
answer-correctness evals, adversarial review, access control; 19-min ingest for 20 tables;
default-on PostHog telemetry whose error reports include raw error messages.

Strategic read:
- **They do NOT have:** any verification of answers, signed/portable receipts, cryptographic
  provenance (evidence dirs are local + uncommitted), CDC/freshness/revocation, multi-tenant
  trust, anything outside warehouse-SQL scope. Their convergence risk is HIGH on
  analytics-answer verification (substrate is receipt-shaped; watch Spider 2 publication,
  "receipt"/"signed" release language, access control landing in OSS) but LOW on our full rail.
- **Copy candidates:** the <10-min agent-queries-real-data onboarding bar (setup wizard that
  also writes `.claude`/`.cursor` rules + hosted demo warehouse), the YAML-vs-Markdown
  context split rule, the 7-action reviewable-diff vocabulary, `usage_mode: always/auto/never`
  retrieval governance, value→column `dictionary_search`, bounty-labeled connector issues.
- **Wrap shapes (Apache-2.0, read-only by construction):** (1) `ktx ingest` as a pre-LLM
  normalization Action whose outputs Baltor verifies/signs/CDCs; (2) the MCP tools behind a
  Baltor gate (ktx proposes, Baltor disposes — `sl_query include:["sql","plan"]` is the
  receipt material); (3) `ktx-sl` Python engine alone as a deterministic semantic-SQL
  compiler primitive. Sandbox policy: force `KTX_TELEMETRY_DISABLED=1`.

## Cross-lane top threats (both sweeps merged)

| # | Company | Batch | Threat | One line |
|---|---|---|---|---|
| 1 | Airbyte | W20 | 5 | Incumbent pivoted onto the literal "context layer for AI agents" tagline; movement ≠ assurance is the counter |
| 2 | Mem0 | S24 | 4 | $24M "memory layer" mindshare; buyers conflate memory with governed context |
| 3 | Reducto | W24 | 4 | $108M, Fortune-10 regulated-document ingestion one step upstream of our rail |
| 4 | Zep (Graphiti) | W24 | 4 | Bi-temporal fact validity = closest technical overlap with our CDC/truth lifecycle |
| 5 | Respan (fka Keywords AI) | W24 | 4 | **The foil to name**: "self-driving" obs+evals+gateway that lets the loop fix itself — agents dispose; no receipts |
| 6 | Mastra | W25 | 4 | $35M TS framework owning runtime mindshare — Teleon positions ABOVE frameworks, receipts/gates over any of them |
| 7 | Composio | not-YC (claim unverified) | 4 | $29M "skills that evolve" = ungoverned capability registry colliding with OHH + capability gateway |
| 8 | Exa | S21 | 3.5 | $85M@$700M grounding source; one trust-scoring feature from "governed web context" |
| 9 | Kaelio | X25 | 3.5 | Above — analytics-truth sibling with receipt-shaped substrate |
| 10 | LiteLLM / Golf / HumanLayer / Multifactor / Openlayer / Confident AI / Coval / Agentic Fabriq | W23–W26 | 3 | Routing, MCP-audit, approval-gates, agent-IAM-audit, CI-gates, OSS evals, simulation, agent-identity — each owns ONE fragment of the rail |

Dead/pivoted/absorbed worth citing as thesis evidence: vanna archived (Feb 2026), Trieve and
Helicone → Mintlify, Langfuse → ClickHouse, Ragas → RL envs, Athina → video ads, Superpowered
→ dead, Chunkr → vision data foundry, Koyeb → Mistral. Bare RAG APIs and standalone evals
did not survive as companies.

## IJFW ("It Just F*cking Works") — FerroxLabs

Real and current: github.com/FerroxLabs/ijfw (184★, MIT, JS; v1.6.0 2026-06-10, v1.6.1
2026-06-11; npm `@ijfw/install` ~1.8k DL/mo; solo-dev Sean Donahoe). A local-first "shared
brain + operating layer" wiring 16 coding agents into one memory (markdown + recency decay +
"dream cycle" promotion/pruning), a brainstorm→plan→execute→verify→ship gate spine, a
"Trident" 3-model cross-audit (consensus/contested tags + cost receipts), smart routing, and
34 skills. Threat: Baltor 2 / Teleon 1 / OHH 1 — vocabulary convergence (receipts, gates,
verify-before-ship), not market collision; its "receipts" are cost telemetry, its verification
is LLMs judging LLMs (proposes AND disposes), and its memory pruning violates our lossless
law (clean differentiation line). Wrap candidates: memory engine behind a port; Trident as a
candidate multi-model audit Action (proposes only); their LongMemEval/Mem0/Letta/Zep
benchmark harness as an OHH harness candidate when the split-out repo surfaces. Also a
thesis validator: their 1.6.0 notes REMOVED an unfounded savings multiplier "for honesty" —
the market rewards defensible numbers.

## Positioning actions this produces (owner-gated where outward-facing)

1. Name the foils precisely in Baltor copy (draft, owner approves): Airbyte = "they deliver
   context; we make it safe to act on"; Respan = "self-driving loops fix themselves; governed
   loops prove themselves"; Mem0/Zep = "memory is what agents believe; Baltor is what's
   verified"; ktx = "trusted SQL shape ≠ verified facts"; IJFW = "cost receipts ≠ evidence."
2. Teleon sits ABOVE runtimes: Mastra/Trigger.dev/Hatchet apps are bounded-agent /
   ExecutionProviderPort candidates; the receipts+gates plane works over any of them.
3. Speak MCP at the Agent Capability Gateway or be routed around (Golf/Metorial/Manufact/
   Composio are making MCP the distribution rail); differentiate on the one artifact nobody
   mints: a signed, replayable receipt behind a deterministic promotion gate.
4. Wrap-candidate queue (all candidate ≠ active, behind ports): Graphiti (temporal graph),
   Reducto/Extend (parsing), Exa/Firecrawl (retrieval/ingest), Recall.ai (meetings), ktx
   (three shapes above), DeepEval/Ragas-lib/Hud evalsets (harness sources), LiteLLM (routing
   backend), IJFW memory/Trident.
5. Watch triggers: Kaelio Spider-2 + "receipt" language; Airbyte governance features; Reducto
   "verified extraction"; Zep governance framing; Respan funding/enterprise motion; the
   2–3-batch window before someone funds the receipts rail.

Full per-company tables with every YC/press URL live in the four sub-reports (session
2026-06-11); this doc is the distilled map. Related memories: [[kaelio-ktx-competitor]],
[[airbyte-context-layer-competitor]], [[codestrap-x-reason-competitor]],
[[teleon-competitive-landscape]], [[supermemory-competitor-complement]].
