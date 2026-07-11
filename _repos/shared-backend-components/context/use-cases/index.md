# Use cases — what you can build today

Eight one-page recipes that show how to compose the hub's primitives
into real production patterns. Each recipe lists: the goal, the exact
components to use, the composition, and the install path for Claude
Code / Cursor / any Agent Skills-compatible host.

## The eight starter use cases

| # | Use case | One-line task | Primary pipeline |
|---|---|---|---|
| 1 | [Internal Q&A on documents](qa-on-documents.md) | Upload PDFs, ask questions, get cited answers | `pipeline/chat-with-pdf-citations` |
| 2 | [Code review with security](code-review.md) | Review a diff with OWASP/CWE citations + risk score | `pipeline/code-review-with-risk-score` |
| 3 | [Deep research with citations](deep-research.md) | Multi-source web research with verified citations | `pipeline/deep-research-with-citations` |
| 4 | [Customer-support email triage](customer-support.md) | Classify intent, draft reply, escalate sensitive | `pipeline/email-triage-and-draft` |
| 5 | [Clinical decision support](clinical-decision-support.md) | Differential diagnosis with red-flag escalation + citations | `pipeline/differential-diagnosis` |
| 6 | [AML transaction review](aml-screening.md) | Sanctions-first review with FATF typology matches | `pipeline/suspicious-transaction-review` |
| 7 | [Brand-safe image generation](image-gen.md) | Style-RAG + lens-physics + safety-screened image gen | `pipeline/brand-safe-product-photo` |
| 8 | [LLM red-teaming](llm-red-team.md) | Prompt-injection + jailbreak + safety probe battery | mix of `rule-pack/grep-*` + `processor/garak-*` |

## The composition pattern they share

Every recipe follows the same layered chain (the DueCare pattern):

```
input
  → identity / cost gate
  → redact PII / secrets
  → guard prompt-injection
  → classify intent / risk
  → query optimization (rewrite / decompose / HyDE)
  → retrieve (BM25 + dense + RRF)
  → rerank (cross-encoder)
  → verify sources (official / authority / freshness)
  → assemble context (persona + framework + schema + LITM-pack)
  → compress (LLMLingua)
  → call LLM
  → parse + repair
  → verify (citations / hallucination / schema)
  → iterative revise (if any verifier fails)
  → audit / cost / provenance
  → deliver
```

Different use cases turn different layers on/off. The kitchen-sink
[`pipeline/everything-research-pipeline`](https://Amarel-Taylor-Scott.github.io/openhubforai/catalog/pipeline_everything-research-pipeline/)
shows all 22 passes for reference.

## How to use a recipe

1. **Read the recipe** to see which primitives are needed.
2. **Install via the Claude Code plugin marketplace**:
   ```
   /plugin marketplace add Amarel-Taylor-Scott/openhubforai@dist-published
   /plugin install openhubforai-skills
   ```
3. **Or copy a single skill** directly to `~/.claude/skills/`.
4. **Or fork the pipeline manifest** and edit defaults (model adapter, knowledge packs, rule packs) to match your environment.

## Adding a new use case

Open a PR with a new `docs/use-cases/<slug>.md` following the recipe
template. Include: goal, when-to-use, primitives list, composition
diagram, sample run, customization options.
