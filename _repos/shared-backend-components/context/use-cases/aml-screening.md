# Use case 6 - AML transaction review

> Sanctions-first transaction review with FATF typology matches and SAR-style narrative drafts.

## When to use

- Bank / fintech AML investigations team
- Crypto exchange transaction monitoring
- Money-services-business compliance
- Auditor preparation

## Primary pipeline

[`pipeline/suspicious-transaction-review`](../catalog/pipeline_suspicious-transaction-review.md)

## Primitives used

| Layer | Component |
|---|---|
| Privacy | `rule-pack/financial-pii-en` (IBAN, SWIFT, PAN+Luhn, SSN/EIN, account#) |
| Sanctions | `rule-pack/sanctions-screening` (OFAC SDN, UN, EU, HMT, PEP lists) |
| Tool | `tool/sanctions-check` |
| Tool | `tool/transaction-graph-query` |
| RAG | `knowledge-pack/fatf-typologies-sample` (composite paraphrases) |
| RAG | `knowledge-pack/aml-red-flags-extended` (28 observable indicators) |
| RAG | `knowledge-pack/sanctions-list-shape` (data shape, populate with live OFAC/UN data) |
| Classifier | `rule-pack/aml-typologies-fatf` (structuring, layering, TBML, geographic, rapid pass-through) |
| Persona | `persona/aml-analyst` (no intent assertions; describe patterns) |
| Harness | `harness/aml-investigation` |

## Composition (sanctions-FIRST, then typology)

```
narrative + transactions + related_entities
  → redact-pii-text (financial PII)
  → sanctions-screen-entities (OFAC + UN + EU)
     ↓
     IF sanctions_hit: escalate_to_OFAC; halt routine review
     ↓
  → transaction-graph-query (2-hop, 30-day window)
  → typology-score (FATF: structuring / layering / TBML / geographic / round-dollar)
  → retrieve fatf-typologies-sample (cited paragraphs)
  → aml-investigation harness (persona/aml-analyst)
  → sanctions_hits[], typology_matches[], narrative_draft, risk_score, escalation
```

## Sample inputs / outputs

```python
inputs = {
  "account_id": "ACCT-PLACEHOLDER-001",
  "narrative":  "Account opened 90 days ago. 12 cash deposits of $9,500 across 3 branches in 14 days, then a single outgoing wire of $114,000 to a new beneficiary.",
  "transactions": [...],
  "related_entities": [...]
}
# → sanctions_hits: []  # no OFAC match
# → typology_matches:
#     [{ typology_id: "structuring_under_threshold",
#        fatf_section: "fatf-structuring-§2.1",
#        supports: [...],
#        evidence_edges: [...] }]
# → narrative_draft: "## DRAFT - Suspicious Activity Narrative\n\n..."
# → risk_score: 0.74
# → escalation: "enhanced_due_diligence"
```

## Install path

### Claude Code

```
/plugin marketplace add Amarel-Taylor-Scott/openhubforai@dist-published
/suspicious-transaction-review
```

### Production deploy (FedRAMP / SOC-2 environment)

1. Replace `knowledge-pack/sanctions-list-shape` data files with the live OFAC SDN, UN consolidated, EU sanctions, and HMT lists. Schedule daily refresh.
2. Replace `knowledge-pack/fatf-typologies-sample` with your institution's full FATF + FinCEN advisory corpus.
3. Wire `tool/transaction-graph-query` to your transaction-graph DB (Neo4j / TigerGraph / Memgraph).
4. Set `eu_ai_act_risk: high_risk` on the pipeline if you deploy in the EU and the system materially affects access to financial services. CI will emit the EU AI Act Annex IV dossier.
5. Wire `processor/escalate-human-review` to your case management (Actimize, NICE, etc.).

## Customization knobs

- **Crypto-specific add-ons**: write `knowledge-pack/crypto-mixers` (Tornado Cash, etc.) + `rule-pack/grep-crypto-wallets` for blockchain analytics.
- **Sector-specific typologies**: e.g. correspondent banking has different red flags than retail. Layer a sector pack.
- **Frontier judge for QA**: add a `processor/llm-judge` step with the `frontier_judge` target - but only after PII redaction.

## Important disclaimer

The narrative output is labeled **DRAFT** and is **NOT a SAR filing**.
Final SAR review and filing requires a BSA officer per institutional
policy and applicable jurisdiction certification. The persona refuses
to assert intent about named individuals.
