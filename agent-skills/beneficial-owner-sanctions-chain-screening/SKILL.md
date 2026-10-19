---
name: beneficial-owner-sanctions-chain-screening
description: Given a corporate counterparty (name + jurisdiction), resolve its ownership/control
  chain, screen every node against sanctions/PEP lists, apply the aggregated-ownership
  (≥50%) and control tests, and decide whether the counterparty is blocked/high-risk
  by virtue of a sanctioned UBO — emitting a yes/no with the cited chain and the controlling
  node. Halt to escalation on any sanctioned node.
when_to_use: 'Pipeline kind: research_entity.'
---

# Beneficial-owner sanctions-chain screening (50%/control)

Resolve the ownership / control chain of a corporate counterparty and
decide whether a sanctioned or politically-exposed ultimate beneficial
owner (UBO) sits behind it — applying the aggregated-ownership and
control tests used in sanctions compliance (e.g. OFAC's 50 Percent
Rule and control-based designation) — and produce a cited yes/no with
the traversed chain.

Negative space: a bare model cannot walk a corporate ownership graph,
cannot apply the aggregated-50%/control test, and cannot tell you
WHICH intermediate entity is the sanctioned node — it has no registry
access and confabulates ownership. The chain comes from a registry
lookup tool + entity linking; each hop is screened deterministically;
the model only narrates the resolved chain and applies the
control/ownership test against retrieved framework text, citing each
conclusion. Indirect ownership through a sanctioned parent makes the
counterparty blocked even when the counterparty itself is not listed —
the exact reasoning step base models miss.

Reference / educational only — registry results and chains are
synthetic / governed snapshots; not legal advice. Bundle: High-
precision legal / regulated RAG over a sanctions-ownership corpus.

## Task

Given a corporate counterparty (name + jurisdiction), resolve its
ownership/control chain, screen every node against sanctions/PEP
lists, apply the aggregated-ownership (≥50%) and control tests, and
decide whether the counterparty is blocked/high-risk by virtue of a
sanctioned UBO — emitting a yes/no with the cited chain and the
controlling node. Halt to escalation on any sanctioned node.

## Steps

1. **registry_lookup** — `tool` → `tool/opencorporates-lookup`
2. **link_entities** — `tool` → `tool/entity-recognition-linker`
3. **canonicalize_owner_names** — `processor` → `processor/name-canonicalize`
4. **screen_counterparty** — `tool` → `tool/sanctions-check`
5. **screen_chain_nodes** — `tool` → `tool/sanctions-check`
6. **retrieve_framework** — `knowledge_pack` → `knowledge-pack/sanctions-ownership-chain-frameworks`
7. **apply_ownership_test** — `harness` → `harness/sanctions-ownership-chain-review`
8. **calibrate_severity** — `processor` → `processor/severity-calibrator`
9. **check_citations** — `processor` → `processor/citation-span-checker`
10. **escalate** — `processor` → `processor/escalate-human-review` (when `$.steps.screen_counterparty.output.matches != [] || $.steps.screen_chain_nodes.output.matches != []`)
11. **audit** — `processor` → `processor/audit-trace-emitter`

## Defaults

- **persona**: persona/trade-compliance-officer
- **model_adapter**: adapter/ollama-default
- **knowledge_packs**: `knowledge-pack/sanctions-ownership-chain-frameworks`, `knowledge-pack/sanctions-list-shape`
- **rule_packs**: `rule-pack/financial-pii-en`, `rule-pack/sanctions-screening`

## Success criteria

- rubric `rubric/sanctions-ownership-chain-quality-v1` threshold 0.78
- deterministic `$.steps.check_citations.output.result.pass` == `True`
- deterministic `$.outputs.blocked_by_ubo` in `[True, False]`

## Provenance

- Hub component: `pipeline/beneficial-owner-sanctions-chain-screening` v0.1.0
- License: `MIT`
- Industry: finance, finance.kyc, trade.sanctions
- Full source manifest: see `references/manifest.yaml`
