# Primitive Problem-Solution Details Handoff

Last updated: 2026-07-01

Audience: Claude 5 Fable, Codex, Claude Code, and model lanes turning ranked
primitive opportunities into buildable primitive cards, groups, routes, tests,
and promotion evidence.

Status: generated seed detail layer. These rows are candidate planning
artifacts, not promoted truth.

## Core Answer

Yes: track more than primitive descriptions. Do it as linked
problem-solution detail records, not by bloating every compact primitive card.

The compact primitive card should stay optimized for search and routing:

```text
input edge
output edge
blackbox behavior
effects
runtime targets
proof status
candidate/truth boundary
```

The problem-solution detail card should hold the deeper operational context:

```text
problem frame
user triggers
stakes and non-goals
solution route
transformations
implementation notes
acceptance criteria
proof plan
failure modes
troubleshooting hooks
negative memory queries
synthetic example input/output
```

That gives agents enough specificity to implement or repair a primitive without
forcing every search result to carry a long narrative.

## Seed Pack

The generated pack is:

```text
catalog/knowledge-packs/data/primitive-problem-solution-details/
```

It contains:

- `problem_solution_details_1000.jsonl` with one detail record for each ranked
  high-priority primitive opportunity;
- `solution_patterns.jsonl` with 9 reusable problem-solution route patterns;
- `detail_template.json` with the required sections;
- `manifest.json` with pack counts and source status.

The generator is:

```bash
python3 scripts/generate_primitive_problem_solution_details.py
```

The checker is:

```bash
python3 scripts/check_primitive_problem_solution_details.py --self-test
```

## Relationship To Ranked Opportunities

The high-priority opportunity row answers:

```text
Which module, industry, variant, input edge, output edge, source hints,
proof requirements, and materialization policy should be prioritized?
```

The problem-solution detail row answers:

```text
Why does this problem matter?
What does a reusable solution route look like?
What should be deterministic?
Where may a model help?
What must be proven?
What usually fails?
How should an agent troubleshoot it?
What synthetic input/output should seed fixtures?
```

Every detail row links back to one ranked `opportunity_id`. Do not promote a
detail row into truth just because it is complete; it still needs source refs,
license or terms review when applicable, contract tests, fixture receipts, and
receipt validation.

## Solution Patterns

The first reusable route patterns are:

```text
verify_before_answer
resolve_enrich_then_receipt
jurisdiction_ladder
freshness_monitor
quality_gate_then_quarantine
risk_signal_review_packet
graph_extract_with_evidence
license_terms_gate
proof_receipt_pipeline
```

Use these to keep details consistent across thousands of industries, countries,
schemas, websites, cloud marketplaces, and agent graph paths.

## Compact Card Versus Detail Card

Put this in the compact primitive card:

- the visible input and output edge;
- one blackbox behavior sentence;
- effects and runtime targets;
- proof status;
- source refs once verified;
- links to group, route, overlay, and detail records.

Put this in the problem-solution detail card:

- real user situations that trigger the primitive;
- stakes, non-goals, and policy constraints;
- deterministic route steps and allowed model use;
- transformations and data contracts;
- acceptance criteria;
- proof plan and fixture plan;
- failure modes and troubleshooting hooks;
- negative memory queries;
- synthetic examples.

This split preserves the nesting-doll context rule: show the smallest useful
contract first, then drill down only when planning, repair, proof, or
implementation needs more context.

## Promotion Rule

All rows stay:

```json
{
  "candidate": true,
  "serves_truth": false
}
```

until a separate promotion path attaches source refs, validates contracts,
checks policy and license obligations, runs fixtures, records receipts, and
approves the primitive or group for truth-serving use.

## Validation

Run:

```bash
python3 scripts/generate_primitive_problem_solution_details.py
python3 scripts/check_primitive_problem_solution_details.py --self-test
```

The checker requires:

- 1,000 detail records;
- 9 solution patterns;
- one detail for every ranked opportunity;
- candidate and truth-boundary fields on every row;
- required problem, solution, implementation, proof, failure, troubleshooting,
  negative-memory, and example sections;
- empty `source_refs` until verified source resolution exists.
